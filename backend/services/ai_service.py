"""
services/ai_service.py  (v2 — conversation memory integrated)
Thin abstraction layer over different LLM providers.
-------------------------------------------------------------
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
"""

import logging
import textwrap
from typing import Literal

from config.settings import get_settings
from models.schemas  import BuiltPrompt, LLMRawResponse

logger = logging.getLogger(__name__)


# ── Mock responses (unchanged from v1) ───────────────────────────────────────

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

    v2 pipeline (process method):
        user message + session_id
          └─► MemoryStore.add(user message)         [step 1]
          └─► MemoryStore.get(history)              [step 2]
          └─► PromptBuilder.build_with_history()    [step 3]
          └─► _call_llm()                           [step 4]
          └─► SafetyFilter.filter()                 [step 5]
          └─► MemoryStore.add(assistant reply)      [step 6]
          └─► MemoryStore.trim()                    [step 7]
          └─► ChatResponse
    """

    def __init__(self) -> None:
        from services.symptom_extractor import SymptomExtractor
        from services.prompt_builder    import PromptBuilder
        from services.safety_filter     import SafetyFilter
        from services.memory_store      import MemoryStore   # ← NEW in v2

        self.settings       = get_settings()
        self.extractor      = SymptomExtractor()
        self.prompt_builder = PromptBuilder()
        self.safety_filter  = SafetyFilter()
        self.memory         = MemoryStore()                  # ← NEW in v2

    # ── Public API ────────────────────────────────────────────────

    async def process(self, user_message: str, session_id: str) -> dict:  # ← session_id added
        """
        Full v2 pipeline: message + session → structured response.

        Args:
            user_message: Raw text from the user.
            session_id:   Stable identifier for this conversation.

        Returns:
            Dict matching ChatResponse schema.
        """
        logger.info(
            "Processing message | session=%s | length=%d",
            session_id, len(user_message),
        )

        # ── Step 1: store the incoming user message ───────────────
        self.memory.add(session_id, role="user", content=user_message)

        # ── Step 2: extract symptoms from current message ─────────
        # (Extraction still runs on the current message only — the LLM
        #  will use history for context, not the extractor.)
        extracted = self.extractor.extract(user_message)
        logger.debug("Extracted symptoms: %s", extracted)

        # ── Step 3: retrieve history and build prompt ─────────────
        # get() returns all messages including the one we just added.
        # We exclude the last message (current user turn) from the
        # "history" block so it appears under "Current message:" instead.
        all_messages = self.memory.get(session_id)
        prior_history = all_messages[:-1]  # everything before the current message

        built_prompt: BuiltPrompt = self.prompt_builder.build_with_history(
            user_message=user_message,
            extracted=extracted,
            history=prior_history,
        )

        # ── DEBUG: print the full joined prompt ──────────────────────
        # Shows exactly what gets sent to the LLM. Remove in production.
        # logger.debug("SYSTEM PROMPT:\n%s", built_prompt.system_prompt)
        # logger.debug("USER PROMPT (history + current message joined):\n%s", built_prompt.user_prompt)

        # ── Step 4: call the LLM ──────────────────────────────────
        raw: LLMRawResponse = await self._call_llm(built_prompt)
        logger.debug("LLM response (%s): %.120s…", raw.model_used, raw.raw_text)

        # ── Step 5: apply safety filter ───────────────────────────
        result = self.safety_filter.filter(raw.raw_text)
        if result.was_modified:
            logger.warning(
                "Safety filter modified response | session=%s | message=%.80s…",
                session_id, user_message,
            )

        # ── Step 6: store the assistant reply in memory ───────────
        self.memory.add(session_id, role="assistant", content=result.reply)

        # ── Step 7: trim history to last 6 messages ───────────────
        self.memory.trim(session_id)

        return {
            "reply":     result.reply,
            "extracted": extracted,
            "safe":      not result.was_modified,
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
                f"Unknown LLM_PROVIDER: '{provider}'. Expected openai | anthropic | mock."
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
            raise RuntimeError(
                "google-genai not installed. Run: pip install google-genai"
            )

        client = genai.Client(api_key=self.settings.GEMINI_API_KEY)

        combined_prompt = f"""
    {prompt.system_prompt}

    User message:
    {prompt.user_prompt}
    """

        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=combined_prompt
        )

        text = response.text or ""

        return LLMRawResponse(
            raw_text=text.strip(),
            model_used=self.settings.GEMINI_MODEL
        )

    # ── Mock ──────────────────────────────────────────────────────

    def _call_mock(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """Unchanged from v1."""
        global _mock_index
        reply = _MOCK_REPLIES[_mock_index % len(_MOCK_REPLIES)]
        _mock_index += 1
        return LLMRawResponse(raw_text=reply.strip(), model_used="mock-v1")
