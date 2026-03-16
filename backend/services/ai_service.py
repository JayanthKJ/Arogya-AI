"""
services/ai_service.py
-----------------------
Thin abstraction layer over different LLM providers.

Supported providers (controlled by LLM_PROVIDER in .env):
  "openai"     — OpenAI Chat Completions API
  "anthropic"  — Anthropic Messages API
  "mock"       — Deterministic mock replies (development / CI)

Adding a new provider means:
  1. Add a new `elif` branch in _call_llm()
  2. Add its SDK to requirements.txt
  Nothing else changes.
"""

import logging
import textwrap
from typing import Literal

from config.settings import get_settings
from models.schemas import BuiltPrompt, LLMRawResponse

logger = logging.getLogger(__name__)

# ── Mock responses (development only) ────────────────────────────────────────
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


class AIService:
    """
    Orchestrates the full AI pipeline for a single user message:

        raw text
          └─► SymptomExtractor  → ExtractedSymptoms
          └─► PromptBuilder     → BuiltPrompt
          └─► _call_llm()       → LLMRawResponse
          └─► SafetyFilter      → FilterResult
          └─► ChatResponse

    The route handler calls `process()` and receives a ready-to-send response.
    """

    def __init__(self) -> None:
        from services.symptom_extractor import SymptomExtractor
        from services.prompt_builder    import PromptBuilder
        from services.safety_filter     import SafetyFilter

        self.settings         = get_settings()
        self.extractor        = SymptomExtractor()
        self.prompt_builder   = PromptBuilder()
        self.safety_filter    = SafetyFilter()

    # ── Public API ────────────────────────────────────────────────

    async def process(self, user_message: str):
        """
        Full pipeline: message → structured response.

        Returns a dict compatible with ChatResponse schema.
        Raises RuntimeError on unrecoverable LLM errors.
        """
        logger.info("Processing message (length=%d)", len(user_message))

        # Step 1 — Extract symptoms
        extracted = self.extractor.extract(user_message)
        logger.debug("Extracted: %s", extracted)

        # Step 2 — Build prompt
        built_prompt: BuiltPrompt = self.prompt_builder.build(user_message, extracted)

        # Step 3 — Call LLM
        raw: LLMRawResponse = await self._call_llm(built_prompt)
        logger.debug("LLM raw response (%s): %.120s…", raw.model_used, raw.raw_text)

        # Step 4 — Safety filter
        result = self.safety_filter.filter(raw.raw_text)
        if result.was_modified:
            logger.warning("Safety filter modified response for message: %.80s…", user_message)

        return {
            "reply":     result.reply,
            "extracted": extracted,
            "safe":      not result.was_modified,
        }

    # ── LLM dispatch ─────────────────────────────────────────────

    async def _call_llm(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """Route to the correct LLM provider based on settings."""
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
            raise ValueError(f"Unknown LLM_PROVIDER: '{provider}'. Expected openai | anthropic | gemini | mock.")

    # ── OpenAI ────────────────────────────────────────────────────

    async def _call_openai(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """
        Call the OpenAI Chat Completions API (async).
        Requires: pip install openai
        """
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError(
                "openai package not installed. Run: pip install openai"
            )

        client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=self.settings.OPENAI_MODEL,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            temperature=self.settings.LLM_TEMPERATURE,
            messages=[
                {"role": "system",  "content": prompt.system_prompt},
                {"role": "user",    "content": prompt.user_prompt},
            ],
        )

        text = response.choices[0].message.content or ""
        return LLMRawResponse(raw_text=text.strip(), model_used=self.settings.OPENAI_MODEL)

    # ── Anthropic ─────────────────────────────────────────────────

    async def _call_anthropic(self, prompt: BuiltPrompt) -> LLMRawResponse:
        """
        Call the Anthropic Messages API (async).
        Requires: pip install anthropic
        """
        try:
            import anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            )

        client = anthropic.AsyncAnthropic(api_key=self.settings.ANTHROPIC_API_KEY)

        message = await client.messages.create(
            model=self.settings.ANTHROPIC_MODEL,
            max_tokens=self.settings.LLM_MAX_TOKENS,
            system=prompt.system_prompt,
            messages=[
                {"role": "user", "content": prompt.user_prompt},
            ],
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
        """
        Return rotating mock replies for local development.
        No API key or network connection needed.
        """
        global _mock_index
        reply = _MOCK_REPLIES[_mock_index % len(_MOCK_REPLIES)]
        _mock_index += 1
        return LLMRawResponse(raw_text=reply.strip(), model_used="mock-v1")
