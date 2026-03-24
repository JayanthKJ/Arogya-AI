"""
services/prompt_builder.py  (v3 — interpreted context added)
-------------------------------------------------------------
Builds the system and user prompts that are sent to the LLM.

Responsibilities:
  1. Define Arogya AI's identity, tone, and safety boundaries.
  2. Enrich the user prompt with the structured symptom context so the
     LLM can give more relevant guidance without needing to re-parse text.
  3. Keep the system prompt short and direct — LLMs follow concise
     instructions more reliably than long paragraphs.
CHANGE LOG (v2):
  - Added `build_with_history(user_message, extracted, history)` method
  - Original `build()` method is UNCHANGED — existing callers are unaffected
  - Added _format_history() private helper
CHANGE LOG (v3):
  - build_with_history(): added `interpreted` parameter
  - _build_user_prompt_with_history(): added Section 4 — interpreted health context
  - build() and all other methods: UNCHANGED
"""

from __future__ import annotations

from models.schemas import ExtractedSymptoms, BuiltPrompt

# Import the Message dataclass from memory_store for type hints only.
# No business logic from memory_store enters this file.
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.memory_store import Message


# ── System prompt template (unchanged from v1) ─────────────────────────────────────────
# This is the "persona" injected at the top of every LLM conversation.
# It is intentionally conservative to keep the AI within safe bounds.

_SYSTEM_PROMPT = """You are Arogya AI, a compassionate and knowledgeable health guidance assistant designed to help people — especially elderly users — understand their health better.

YOUR CORE PRINCIPLES:
1. NEVER provide a medical diagnosis or claim to diagnose any condition.
2. NEVER prescribe, recommend, or name specific medications or dosages.
3. ALWAYS remind users to consult a qualified doctor for any serious, persistent, or worsening symptoms.
4. Provide clear, simple, general health information and lifestyle guidance only.
5. Use warm, respectful, easy-to-understand language suitable for all ages.
6. If symptoms sound potentially serious (chest pain, difficulty breathing, stroke signs, etc.), advise the user to seek emergency care immediately.
7. Keep responses concise: 3-5 short paragraphs maximum.
8. End every response with a doctor-consultation reminder unless the user is asking a trivially general question.
9. Do NOT assume or introduce new symptoms that were not mentioned by the user.
10. Focus on the emergency contacts based in India if any serious symptoms show up."""

# ── Symptom context block (unchanged from v1) ─────────────────────────────────
# Injected into the user prompt when symptoms are detected.

_SYMPTOM_CONTEXT_TEMPLATE = """
[Structured context extracted from user's message]
- Mentioned symptoms : {symptoms}
- Duration mentioned : {duration}
- Body parts mentioned: {body_parts}
- Severity hints      : {severity}

Please use this context to personalise your guidance.
---
User's original message:
"""

# ── Emergency symptoms keywords (trigger extra-urgent advice) (unchanged from v1) ────────────────────────────────────

_EMERGENCY_SYMPTOMS = {
    "chest pain", "chest tightness", "difficulty breathing",
    "shortness of breath", "stroke", "paralysis", "unconscious",
    "fainting", "seizure", "severe bleeding", "coughing blood",
    "blood in stool", "sudden vision loss",
}

# ── Builder class ─────────────────────────────────────────────────────────────

class PromptBuilder:
    """
    Stateless builder — instantiate once and reuse.

    Public methods:
      build()              — single-turn (no history), original behaviour.
      build_with_history() — multi-turn, injects history + interpreted context.
    """

    # ── v3: multi-turn method ─────────────────────────────────────────────────

    def build_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      list[dict],
        interpreted:  dict | None = None,   # <- NEW, optional for safety
    ) -> BuiltPrompt:
        """
        Build a prompt with conversation history and interpreted health context.

        Prompt structure:
        ┌─────────────────────────────────────────────────────┐
        │  [System prompt]                                    │
        │                                                     │
        │  Conversation so far:                               │
        │  User: ...  /  Assistant: ...                       │
        │                                                     │
        │  Current message:                                   │
        │  User: <current message>                            │
        │                                                     │
        │  [Extracted symptom context — if any]               │
        │                                                     │
        │  [Interpreted health context — if any]   <- NEW     │
        └─────────────────────────────────────────────────────┘
        """
        system = self._build_system_prompt(extracted)
        user   = self._build_user_prompt_with_history(
            user_message, extracted, history, interpreted
        )
        return BuiltPrompt(system_prompt=system, user_prompt=user)

    def _build_user_prompt_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      list[dict],
        interpreted:  dict | None = None,   # <- NEW
    ) -> str:
        """
        Assemble the full user-facing prompt string across four sections.
        """
        parts: list[str] = []

        # ── Section 1: prior conversation turns ──────────────────
        if history:
            parts.append("Conversation so far:")
            for turn in history:
                # Handle Message objects (current design)
                if hasattr(turn, "role") and hasattr(turn, "content"):
                    label = turn.role.capitalize()
                    content = turn.content
                else:
                    # Fallback: in case old dict format ever appears
                    label = turn["role"].capitalize()
                    content = turn["content"]

                parts.append(f"{label}: {content}")

            parts.append("")  # blank line separator
            parts.append("Analyze how the user's condition has evolved across the conversation before responding.")

        # ── Section 2: current message ───────────────────────────
        parts.append("Current message:")
        parts.append(f"User: {user_message}")

        # ── Section 3: extracted symptom context (unchanged) ─────
        if extracted.symptoms or extracted.duration:
            parts.append("")
            parts.append("[Extracted context from current message]")
            if extracted.symptoms:
                parts.append(f"- Symptoms  : {', '.join(extracted.symptoms)}")
            if extracted.duration:
                parts.append(f"- Duration  : {extracted.duration}")
            if extracted.body_parts:
                parts.append(f"- Body parts: {', '.join(extracted.body_parts)}")
            if extracted.severity_hints:
                parts.append(f"- Severity  : {', '.join(extracted.severity_hints)}")

        # ── Section 4: interpreted health context ─────────────────  <- NEW
        if interpreted and isinstance(interpreted, dict):
            parts.append("")
            parts.append("[IMPORTANT: Interpreted health context — use this to understand progression]")

            symptoms_str = ", ".join(interpreted["symptoms"]) if interpreted["symptoms"] else "none detected"
            parts.append(f"- Symptoms : {symptoms_str}")
            parts.append(f"- Severity : {interpreted['severity']}")
            parts.append(f"- Trend    : {interpreted['trend']}")
            parts.append(f"- Duration : {interpreted['duration']}")     # some improvisations are done after this line.
            parts.append("")
            parts.append("Use this interpreted context to understand how the user's condition is evolving over time.")
            parts.append("Prioritize this over assumptions. Do NOT introduce new symptoms.")        # again some improvisations but in the same version.
            parts.append("This interpreted context is the most reliable structured understanding of the user's condition.")
            parts.append("You MUST base your reasoning primarily on this.")
            parts.append("")
            parts.append("[Response Guidelines]")
            parts.append("- Base your response on the interpreted trend and severity.")
            parts.append("- If trend is worsening, emphasize caution and monitoring.")
            parts.append("- If severity is severe, clearly advise seeking medical attention.")
            parts.append("- If symptoms are unclear, ask clarifying questions.")
            parts.append("- Do NOT contradict the interpreted context.")

        return "\n".join(parts)

    # ── Original single-turn method (unchanged) ───────────────────────────────

    def build(self, user_message: str, extracted: ExtractedSymptoms) -> BuiltPrompt:
        """Single-turn prompt builder. Unchanged from v1."""
        system = self._build_system_prompt(extracted)
        user   = self._build_user_prompt(user_message, extracted)
        return BuiltPrompt(system_prompt=system, user_prompt=user)

    # ── Private helpers (unchanged) ───────────────────────────────────────────

    def _build_system_prompt(self, extracted: ExtractedSymptoms) -> str:
        """
        Base system prompt with an optional emergency notice.
        Shared by both build() and build_with_history().
        Append an emergency notice to the base system prompt when
        potentially urgent symptoms are detected.
        """
        system = _SYSTEM_PROMPT

        detected_emergency = _EMERGENCY_SYMPTOMS.intersection(
            {s.lower() for s in extracted.symptoms}
        )
        if detected_emergency:
            system += (
                "\n\nCRITICAL: The user has mentioned potentially serious symptoms "
                f"({', '.join(detected_emergency)}). "
                "Begin your response by strongly advising them to seek immediate medical attention."
            )

        return system

    def _build_user_prompt(
        self, user_message: str, extracted: ExtractedSymptoms
    ) -> str:
        """
        Single-turn user prompt (v1 behaviour, unchanged).
        Prepends symptom context block if symptoms were found.
        What it does:
        If symptoms were detected, prepend structured context so the LLM
        has clean, parsed data alongside the original free-text message.
        If nothing was extracted, just pass the message through.
        """
        if not extracted.symptoms and not extracted.duration:
            return user_message

        symptoms_str   = ", ".join(extracted.symptoms)       if extracted.symptoms       else "not specified"
        duration_str   = extracted.duration                   if extracted.duration       else "not mentioned"
        body_parts_str = ", ".join(extracted.body_parts)      if extracted.body_parts     else "not mentioned"
        severity_str   = ", ".join(extracted.severity_hints)  if extracted.severity_hints else "not mentioned"

        context = _SYMPTOM_CONTEXT_TEMPLATE.format(
            symptoms=symptoms_str,
            duration=duration_str,
            body_parts=body_parts_str,
            severity=severity_str,
        )
        return context + user_message
