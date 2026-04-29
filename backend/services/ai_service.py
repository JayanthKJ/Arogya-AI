from __future__ import annotations

import logging
import textwrap
from typing import Optional
from typing import Literal

from sqlmodel import Session, select

from config.settings import get_settings
from models.schemas import (
    ChatResponse,
    ExtractedSymptoms,
    BuiltPrompt,
    LLMRawResponse,
)
from models.db_models import ChatMessage
from services.symptom_extractor import SymptomExtractor
from services.symptom_interpreter import SymptomInterpreter
from services.prompt_builder import PromptBuilder
from services.safety_filter import SafetyFilter

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

MAX_LIMITS = 6 # maximum number of messages being sent from earlier conversation till now.

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

    def __init__(self):
        self.settings = get_settings()
        self.extractor = SymptomExtractor()
        self.interpreter = SymptomInterpreter()
        self.prompt_builder = PromptBuilder()
        self.safety_filter = SafetyFilter()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def process(
        self,
        user_message: str,
        session_id: str,
        db: Session,
        user_id: str,
    ) -> ChatResponse:
        # Step 1: Persist user message (scoped to user)
        try:
            db.add(
                ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    role="user",
                    content=user_message,
                )
            )
            db.commit()
        except:
            db.rollback()
            raise

        # Step 2: Fetch full history scoped to BOTH session AND user
        messages: list[ChatMessage] = db.exec(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.user_id == user_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(MAX_LIMITS)
        ).all()

        messages = list(reversed(messages))

        # prior_history = everything except the current (last) message
        prior_history: list[ChatMessage] = messages[:-1]

        normalized_history = [
            {"role": m.role, "content": m.content}
            for m in prior_history
        ]

        logger.debug("Session %s | prior turns=%d", session_id, len(normalized_history))

        # Step 3: Extract symptoms (rule-based, unchanged)
        extracted: ExtractedSymptoms = self.extractor.extract(user_message)
        logger.debug("Extracted: %s", extracted)

        # Step 4: Interpret health context
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

        # Step 4.5: Decision layer (persistent meta disabled for now)
        meta: dict = {}
        prev_state: Optional[dict] = None
        decision = self._decide(interpreted, normalized_history, meta, prev_state)
        logger.debug("Decision: %s", decision)

        # Step 5: Build prompt (prompt_builder expects list-of-dicts)
        built_prompt: BuiltPrompt = self.prompt_builder.build_with_history(
            user_message,
            extracted,
            normalized_history,
            interpreted,
            decision=decision,
        )

        logger.debug("SYSTEM PROMPT:\n%s", built_prompt.system_prompt)
        logger.debug("USER PROMPT:\n%s", built_prompt.user_prompt)

        # Step 6: Call LLM
        raw: LLMRawResponse = await self._call_llm(built_prompt)
        logger.debug("LLM response (%s): %.120s...", raw.model_used, raw.raw_text)

        # Step 7: Safety filter
        result = self.safety_filter.filter(raw.raw_text)
        if result.was_modified:
            logger.warning(
                "Safety filter modified response | session=%s | message=%.80s...",
                session_id, user_message,
            )

        # Step 8: Persist assistant reply (scoped to user)
        try:
            db.add(
                ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    role="assistant",
                    content=result.reply,
                )
            )
            db.commit()
        except:
            db.rollback()
            raise

        return ChatResponse(
            reply=result.reply,
            extracted=extracted,
            interpreted=interpreted,
            safe=result.was_modified is False,
        )

    # ------------------------------------------------------------------
    # Decision logic  (unchanged)
    # ------------------------------------------------------------------

    def _decide(
            self,
            interpreted: dict | None,
            history=None,
            meta: dict = None,
            prev_state: dict | None = None,
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
        trend = interpreted.get("trend", "unknown")
        severity = interpreted.get("severity", "unknown")

        last_decision = meta.get("last_decision")
        prev_trend = prev_state.get("trend") if prev_state else None

        interaction = self._analyze_interaction_state(history or [])
        asked_recently = interaction.get("asked_recently", False)

        # ── Rule 0: HIGH SEVERITY overrides everything ───────────────
        if severity in ["high", "critical"]:
            return {"type": "escalate", "reason": "high_severity"}

        # ── Rule 1: Persistent worsening ─────────────────────────────
        elif trend == "worsening" and prev_trend == "worsening":
            return {"type": "escalate", "reason": "persistent_worsening"}

        # ── Rule 2: New worsening ────────────────────────────────────
        elif trend == "worsening":
            return {"type": "caution", "reason": "new_worsening"}

        # ── Rule 3: Improving ────────────────────────────────────────
        elif trend == "improving":
            return {"type": "respond", "reason": "improving"}

        # ── Rule 4: Avoid repetition ─────────────────────────────────
        elif last_decision == "ask" and confidence != "low":
            return {"type": "respond", "reason": "avoid_repetition"}

        # ── Rule 5: Low confidence ───────────────────────────────────
        elif confidence == "low":
            # Check interaction state to avoid asking twice in a row
            if asked_recently or last_decision == "ask":
                return {"type": "respond", "reason": "already_asked"}
            else:
                return {"type": "ask", "reason": "low_confidence"}

        return {"type": "respond", "reason": "default"}

    def _analyze_interaction_state(self, history) -> dict:
        """
        Extract conversational state:
        - asked_recently: whether assistant asked a question in last turn
        - user_responded: whether user replied after that
        """
        if not history:
            return {"asked_recently": False, "user_responded": False}

        last_assistant = None

        # Find last assistant message (robust to dict or object)
        for msg in reversed(history):
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
            else:
                role = getattr(msg, "role", "")
                content = getattr(msg, "content", "")

            if role == "assistant":
                last_assistant = content
                break

        asked_recently = bool(last_assistant and "?" in last_assistant)

        # Optional: detect if user replied after that
        user_responded = False
        if len(history) >= 2:
            last = history[-1]
            second_last = history[-2]

            last_role = last.get("role") if isinstance(last, dict) else getattr(last, "role", "")
            prev_role = second_last.get("role") if isinstance(second_last, dict) else getattr(second_last, "role", "")

            user_responded = prev_role == "assistant" and last_role == "user"

        return {
            "asked_recently": asked_recently,
            "user_responded": user_responded,
        }
    # ------------------------------------------------------------------
    # LLM dispatch  (unchanged)
    # ------------------------------------------------------------------

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
            f"SYSTEM:\n{prompt.system_prompt}\n\n"
            f"USER:\n{prompt.user_prompt}\n\n"
            f"INSTRUCTIONS:\nFollow all system rules strictly.\n"
            f"Base your reasoning on interpreted context and conversation history.\n"
            f"Do not introduce new symptoms."
        )

        response = client.models.generate_content(
            model=self.settings.GEMINI_MODEL,
            contents=combined_prompt,
        )
        return LLMRawResponse(
            raw_text=response.text.strip(),
            model_used=self.settings.GEMINI_MODEL,
        )

    def _call_mock(self, prompt: BuiltPrompt) -> LLMRawResponse:
        global _mock_index
        reply = _MOCK_REPLIES[_mock_index % len(_MOCK_REPLIES)]
        _mock_index += 1
        return LLMRawResponse(raw_text=reply.strip(), model_used="mock-v1")