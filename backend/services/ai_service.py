"""
services/ai_service.py  (v5 — decision layer added)
-------------------------------------------------------------
Thin abstraction layer over different LLM providers.

CHANGE LOG (v2):
  - __init__: imports and stores a MemoryStore instance
  - process(): accepts `session_id`, runs the 7-step v2 pipeline

CHANGE LOG (v3):
  - __init__: added self.interpreter = SymptomInterpreter()
  - process(): added interpret() call between extraction and prompt building
  - process(): passes interpreted into build_with_history()
  - process(): includes interpreted in the returned dict

CHANGE LOG (v4):
  - process(): removed normalized_history — interpreter receives prior_history directly
  - _call_gemini(): strengthened INSTRUCTIONS block

CHANGE LOG (v5):
  - Added _decide() private method — maps interpreted context to a decision type
  - process(): calls _decide() after interpretation
  - process(): passes decision into build_with_history()
  - API response format UNCHANGED
"""

import logging
import textwrap
from typing import Literal

from config.settings import get_settings
from models.schemas  import BuiltPrompt, LLMRawResponse

from models.db_models import ChatMessage
from sqlmodel import select, Session

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

    v5 pipeline:
        user message + session_id
          └─► MemoryStore.add(user message)              [step 1]
          └─► MemoryStore.get_history(history)           [step 2]
          └─► SymptomExtractor.extract()                 [step 3]
          └─► SymptomInterpreter.interpret()             [step 4]
          └─► _decide()                                  [step 4.5]  <- NEW
          └─► PromptBuilder.build_with_history()         [step 5]
          └─► _call_llm()                                [step 6]
          └─► SafetyFilter.filter()                      [step 7]
          └─► MemoryStore.add(assistant reply) + trim()  [step 8]
          └─► ChatResponse
    """

    def __init__(self) -> None:
        from services.symptom_extractor   import SymptomExtractor
        from services.symptom_interpreter import SymptomInterpreter
        from services.prompt_builder      import PromptBuilder
        from services.safety_filter       import SafetyFilter

        self.settings       = get_settings()
        self.extractor      = SymptomExtractor()
        self.interpreter    = SymptomInterpreter()
        self.prompt_builder = PromptBuilder()
        self.safety_filter  = SafetyFilter()

    # ── Public API ────────────────────────────────────────────────

    async def process(self, user_message: str, session_id: str, db: Session) -> dict:
        """
        Full v5 pipeline: message + session_id -> structured response.
        """
        logger.info(
            "Processing message | session=%s | length=%d",
            session_id, len(user_message),
        )

        # ── Step 1: store user message ────────────────────────────
        db.add(ChatMessage(
            session_id=session_id,
            role="user",
            content=user_message
        ))
        db.commit()

        # ── Step 2: retrieve prior history ────────────────────────
        messages = db.exec(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        ).all()

        prior_history_objs = messages[:-1]

        normalized_history = [
            {"role": m.role, "content": m.content}
            for m in prior_history_objs
        ]

        logger.debug("Session %s | prior turns=%d", session_id, len(normalized_history))

        # ── Step 3: extract symptoms ──────────────────────────────
        extracted = self.extractor.extract(user_message)
        logger.debug("Extracted: %s", extracted)

        # ── Step 4: interpret health context ──────────────────────
        try:
            interpreted = self.interpreter.interpret(
                user_message,
                extracted,
                normalized_history,
            )
        except Exception:
            logger.exception("Interpreter failed — continuing without interpretation")
            interpreted = None

        # guard to check if the interpreter failed
        if not isinstance(interpreted, dict):
            interpreted = None

        logger.debug("Interpreted: %s", interpreted)

        # ── Step 4.5: fetch session meta + decide response strategy ──
        meta = {}
        prev_state = None
        decision = self._decide(interpreted, normalized_history, meta, prev_state)
        logger.debug("Decision: %s", decision)

        # Store decision and interpreted state for next turn
        built_prompt: BuiltPrompt = self.prompt_builder.build_with_history(
            user_message,
            extracted,
            normalized_history,
            interpreted,
            decision=decision,  # <- NEW
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
        db.add(ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result.reply
        ))
        db.commit()

        # API response format unchanged
        return {
            "reply":       result.reply,
            "extracted":   extracted,
            "interpreted": interpreted,
            "safe":        not result.was_modified,
        }

    # ── Decision layer ────────────────────────────────────────────  <- NEW

    def _decide(
        self,
        interpreted: dict | None,
        history:     list = None,
        meta:        dict = None,
        prev_state:  dict | None = None,
    ) -> dict:
        """
        Maps interpreted health context to a strict response strategy.
        Applies priority-ordered rules with full session awareness.

        Priority order (highest → lowest):
          1. Escalation   — worsening trend confirmed across two turns
          2. Caution      — new worsening trend this turn
          3. Improving    — trend is improving → respond normally
          4. Repetition   — already asked last turn → respond
          5. Low conf     — not enough info → ask
          6. Default      — respond
        """
        meta = meta or {}

        # No interpretation available — respond with what we have
        if interpreted is None:
            return {"type": "respond", "reason": "no_interpretation"}

        confidence = interpreted.get("confidence", "low")
        severity   = interpreted.get("severity",   "unknown")
        trend      = interpreted.get("trend",      "unknown")

        last_decision = meta.get("last_decision")
        prev_trend    = prev_state.get("trend") if prev_state else None

        # ── Rule 1: ESCALATE — worsening confirmed across two consecutive turns ─
        # Highest priority — overrides everything else
        if trend == "worsening" and prev_trend == "worsening":
            return {"type": "escalate", "reason": "persistent_worsening"}

        # ── Rule 2: CAUTION — worsening this turn but not confirmed yet ──────────
        if trend == "worsening" and prev_trend != "worsening":
            decision_type = "caution"

        # ── Rule 3: IMPROVING — condition getting better ──────────────────────────
        elif trend == "improving":
            decision_type = "respond"

        # ── Rule 4: REPETITION PREVENTION — already asked last turn ──────────────
        # Only applies when no new symptoms have appeared
        elif last_decision == "ask" and confidence != "low":
            decision_type = "respond"

        # ── Rule 5: LOW CONFIDENCE — need clarification ───────────────────────────
        elif confidence == "low":
            # Check interaction state to avoid asking twice in a row
            state = self._analyze_interaction_state(history or [])
            if state["asked_recently"] or last_decision == "ask":
                decision_type = "respond"
            else:
                decision_type = "ask"

        # ── Rule 6: DEFAULT — normal structured response ──────────────────────────
        else:
            decision_type = "respond"

        return {"type": decision_type}

    def _analyze_interaction_state(self, history) -> dict:
        """
        Extract conversational state:
        - asked_recently: whether assistant asked a question in last turn
        - user_responded: whether user replied after that
        """
        if not history:
            return {
                "asked_recently": False,
                "user_responded": False,
            }

        last_assistant = None
        # Find last assistant message
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_assistant = msg["content"]
                break

        asked_recently = False
        if last_assistant and "?" in last_assistant:
            asked_recently = True

        return {
            "asked_recently": asked_recently,
            "user_responded": True,   # current message exists
        }

    # ── LLM dispatch (unchanged) ──────────────────────────────────

    async def _call_llm(self, prompt: BuiltPrompt) -> LLMRawResponse:
        provider: Literal["openai", "anthropic", "gemini", "mock"] = (
            self.settings.LLM_PROVIDER.lower()
        )
        if provider == "openai":
            return await self._call_openai(prompt)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif provider == "gemini":
           try:
                return await self._call_gemini(prompt)

           except Exception as e:
                error_str = str(e)

                logger.error(f"LLM call failed: {e}")

                # 🔴 Handle Gemini overload / server issues
                if "503" in error_str or "UNAVAILABLE" in error_str:
                    return LLMRawResponse(
                        raw_text="I'm a bit busy right now. Please try again in a few seconds.",
                        model_used="fallback"
                    )

                # 🔴 Handle missing / invalid API key
                if "API key" in error_str or "401" in error_str or "403" in error_str:
                    return LLMRawResponse(
                        raw_text="I'm having trouble connecting right now. Please try again later.",
                        model_used="fallback"
                    )

                # 🔴 Generic fallback
                return LLMRawResponse(
                    raw_text="Something went wrong on my side. Please try again.",
                    model_used="fallback"
                )
        elif provider == "mock":
            return self._call_mock(prompt)
        else:
            raise ValueError(
                f"Unknown LLM_PROVIDER: '{provider}'. Expected openai | anthropic | gemini | mock."
            )

    # ── OpenAI ────────────────────────────────────────────────────

    async def _call_openai(self, prompt: BuiltPrompt) -> LLMRawResponse:
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

        import os
        api_key = self.settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        try:
            from google import genai
        except ImportError:
            raise RuntimeError("google-genai not installed. Run: pip install google-genai")

        client = genai.Client(api_key=api_key)

        combined_prompt = (
            f"SYSTEM:\n{prompt.system_prompt}"
            f"\n\nUSER:\n{prompt.user_prompt}"
            f"\n\nINSTRUCTIONS:"
            f"\nFollow all system rules strictly."
            f"\nBase your reasoning on interpreted context and conversation history."
            f"\nDo not introduce new symptoms."
        )

        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=combined_prompt,
        )

        text = response.text or ""
        return LLMRawResponse(raw_text=text.strip(), model_used=self.settings.GEMINI_MODEL)

    def _call_mock(self, prompt: BuiltPrompt) -> LLMRawResponse:
        global _mock_index
        reply = _MOCK_REPLIES[_mock_index % len(_MOCK_REPLIES)]
        _mock_index += 1
        return LLMRawResponse(raw_text=reply.strip(), model_used="mock-v1")