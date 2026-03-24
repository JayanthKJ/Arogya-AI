"""
services/ai_service.py  (v3 — SymptomInterpreter integrated)
-------------------------------------------------------------
Thin abstraction layer over different LLM providers.

CHANGE LOG (v2):
  - __init__: imports and stores a MemoryStore instance
  - process(): accepts `session_id`, runs the 7-step v2 pipeline
  - _call_llm(): UNCHANGED
  - _call_openai(): UNCHANGED
  - _call_anthropic(): UNCHANGED
  - _call_mock(): UNCHANGED

Supported providers (controlled by LLM_PROVIDER in .env):
  "openai"     — OpenAI Chat Completions API
  "anthropic"  — Anthropic Messages API
  "mock"       — Deterministic mock replies (development / CI)

Adding a new provider means:
  1. Add a new `elif` branch in _call_llm()
  2. Add its SDK to requirements.txt
  Nothing else changes.

The new pipeline (step numbers match requirements doc):
  1. Store user message in memory
  2. Retrieve conversation history for session_id
  3. Pass history into prompt builder (build_with_history)
  4. Call LLM
  5. Apply safety filter
  6. Store assistant response in memory
  7. Trim history to last 6 messages

CHANGE LOG (v3):
  - __init__: added self.interpreter = SymptomInterpreter()
  - process(): added interpret() call between extraction and prompt building
  - process(): passes interpreted into build_with_history()
  - process(): includes interpreted in the returned dict
  - Everything else unchanged.
"""

import logging
import textwrap
from typing import Literal

from config.settings import get_settings
from models.schemas  import BuiltPrompt, LLMRawResponse
from services.memory_store        import memory_store   # Shared in-memory store (single-process only; replace with DB/Redis in production)

logger = logging.getLogger(__name__)


# ── Mock responses (unchanged) ────────────────────────────────────────────────

_MOCK_REPLIES: list[str] = [
    textwrap.dedent("""\
        Thank you for sharing that with me. Based on the symptoms you've described,
        it sounds like you may be experiencing discomfort that deserves attention.

        Generally speaking, symptoms like these can be caused by a range of everyday
        factors — rest, hydration, and a light, balanced diet often help the body
        recover from mild ailments.

        However, it is always important to monitor how you are feeling. If your
        symptoms persist beyond a few days, worsen, or are accompanied by other
        concerns, please do not delay in speaking with your doctor. They are the
        right person to properly evaluate your condition.

        Please take care of yourself, and do not hesitate to seek professional
        medical advice for a proper diagnosis and guidance tailored to your health.
    """),
    textwrap.dedent("""\
        I understand your concern and appreciate you reaching out. What you are
        describing sounds uncomfortable, and it is wise to pay attention to your body.

        In general, maintaining good hydration, adequate rest, and a nutritious diet
        supports the body's natural healing processes. Gentle movement, if tolerable,
        can also be beneficial for many conditions.

        That said, I want to emphasise that only a qualified healthcare professional
        can accurately assess and diagnose your symptoms. Please consult your doctor,
        especially if symptoms are persistent or affecting your daily life.

        Your health matters greatly — please seek professional care for proper guidance.
    """),
]

_mock_index = 0


# ── AIService ─────────────────────────────────────────────────────────────────

class AIService:
    """
    Orchestrates the full AI pipeline for a single user message.

    v3 pipeline:
        user message + session_id
          └─► MemoryStore.add(user message)              [step 1]
          └─► MemoryStore.get(history)                   [step 2]
          └─► SymptomExtractor.extract()                 [step 3]
          └─► SymptomInterpreter.interpret()             [step 4]  <- NEW
          └─► PromptBuilder.build_with_history()         [step 5]
          └─► _call_llm()                                [step 6]
          └─► SafetyFilter.filter()                      [step 7]
          └─► MemoryStore.add(assistant reply) + trim()  [step 8]
          └─► ChatResponse
    """

    def __init__(self) -> None:
        from services.symptom_extractor   import SymptomExtractor
        from services.symptom_interpreter import SymptomInterpreter  # <- NEW
        from services.prompt_builder      import PromptBuilder
        from services.safety_filter       import SafetyFilter

        self.settings       = get_settings()
        self.extractor      = SymptomExtractor()
        self.interpreter    = SymptomInterpreter()                   # <- NEW
        self.prompt_builder = PromptBuilder()
        self.safety_filter  = SafetyFilter()
        self.memory         = memory_store

    # ── Public API ────────────────────────────────────────────────

    async def process(self, user_message: str, session_id: str) -> dict:
        """
        Full v3 pipeline: message + session_id -> structured response.

        Args:
            user_message: Raw text from the user.
            session_id:   Stable identifier for this conversation.

        Returns:
             a dict matching ChatResponse schema (plus interpreted context).
        """
        logger.info(
            "Processing message | session=%s | length=%d",
            session_id, len(user_message),
        )

        # ── Step 1: store user message ────────────────────────────
        self.memory.add(session_id, role="user", content=user_message)

        # ── Step 2: retrieve prior history ────────────────────────
        full_history  = self.memory.get(session_id)
        prior_history = full_history[:-1]   # exclude the message just added
        logger.debug("Session %s | prior turns=%d", session_id, len(prior_history))

        # ── Step 3: extract symptoms ──────────────────────────────
        extracted = self.extractor.extract(user_message)
        logger.debug("Extracted: %s", extracted)

        # ── Step 4: interpret health context ─────────────────────  <- NEW
        normalized_history = [
            {"role": m.role, "content": m.content}
            for m in prior_history
        ]
        try:
            interpreted = self.interpreter.interpret(
                user_message,
                extracted,
                normalized_history,
            )
        except Exception as e:
            logger.exception("Interpreter failed")
            interpreted = None
        logger.debug("Interpreted: %s", interpreted)

        # guard to check if the interpreter failed
        if not isinstance(interpreted, dict):
            interpreted = None

        # ── Step 5: build prompt ──────────────────────────────────
        built_prompt: BuiltPrompt = self.prompt_builder.build_with_history(
            user_message,
            extracted,
            prior_history,
            interpreted,   # <- NEW
        )

        logger.debug("SYSTEM PROMPT:\n%s", built_prompt.system_prompt)
        logger.debug("USER PROMPT:\n%s", built_prompt.user_prompt)

        # ── Step 6: call LLM ──────────────────────────────────────
        raw: LLMRawResponse = await self._call_llm(built_prompt)
        logger.debug("LLM response (%s): %.120s...", raw.model_used, raw.raw_text)

        # ── Step 7: safety filter ─────────────────────────────────
        result = self.safety_filter.filter(raw.raw_text)
        if result.was_modified:
            logger.warning(
                "Safety filter modified response | session=%s | message=%.80s...",
                session_id, user_message,
            )

        # ── Step 8: store assistant reply + trim ──────────────────
        self.memory.add(session_id, role="assistant", content=result.reply)
        self.memory.trim(session_id)

        return {
            "reply":       result.reply,
            "extracted":   extracted,
            "interpreted": interpreted,   # <- NEW
            "safe":        not result.was_modified,
        }

    # ── LLM dispatch — UNCHANGED from v1 ─────────────────────────

    async def _call_llm(self, prompt: BuiltPrompt) -> LLMRawResponse:
        provider: Literal["openai", "anthropic", "gemini", "mock"] = (
            self.settings.LLM_PROVIDER.lower()
        )
        if provider == "openai":
            return await self._call_openai(prompt)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif provider == "gemini":
            return await self._call_gemini(prompt)
        elif provider == "mock":
            return self._call_mock(prompt)
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{provider}'. Expected openai | anthropic | gemini | mock."
            )

    # ── OpenAI ────────────────────────────────────────────────────

    async def _call_openai(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """Unchanged from v1."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        client   = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            temperature=self.settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user",   "content": prompt.user_prompt},
            ],
        )

        text = response.choices[0].message.content or ""
        return LLMRawResponse(raw_text=text.strip(), model_used=self.settings.OPENAI_MODEL)

    # ── Anthropic ────────────────────────────────────────────────────

    async def _call_anthropic(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """Unchanged from v1."""
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

        client  = anthropic.AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=self.settings.ANTHROPIC_MODEL,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            system=prompt.system_prompt,
            messages=[{"role": "user", "content": prompt.user_prompt}],
        )

        # Extract text from the first content block
        text = ""
        for block in message.content:
            if hasattr(block, "text"):
                text = block.text
                break

        return LLMRawResponse(raw_text=text.strip(), model_used=self.settings.ANTHROPIC_MODEL)

    # ── Gemini ─────────────────────────────────────────────────

    async def _call_gemini(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """
        Call Google Gemini API
        Requires: pip install google-genai
        """

        try:
            from google import genai
        except ImportError:
            raise RuntimeError("google-genai not installed. Run: pip install google-genai")

        client = genai.Client(api_key=self.settings.GEMINI_API_KEY)

        combined_prompt = f"""
        SYSTEM:
        {prompt.system_prompt}

        USER:
        {prompt.user_prompt}

        INSTRUCTIONS:
        Follow all system rules strictly.
        """

        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=combined_prompt,
        )

        text = response.text or ""
        return LLMRawResponse(raw_text=text.strip(), model_used=self.settings.GEMINI_MODEL)

    def _call_mock(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """Unchanged from v1."""
        global _mock_index
        reply = _MOCK_REPLIES[_mock_index % len(_MOCK_REPLIES)]
        _mock_index += 1
        return LLMRawResponse(raw_text=reply.strip(), model_used="mock-v1")
