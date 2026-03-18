"""
services/prompt_builder.py  (v2 — adds build_with_history)
-----------------------------------------------------------
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
6. If symptoms sound potentially serious (chest pain, difficulty breathing, stroke signs, etc.), advise the user to seek immediate medical attention.
7. Keep responses concise: 3–5 short paragraphs maximum.
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

    v1 method (unchanged):
        build(user_message, extracted) → BuiltPrompt

    v2 method (new):
        build_with_history(user_message, extracted, history) → BuiltPrompt
    """

    # ── v1 method — UNCHANGED ─────────────────────────────────────

    def build(self, user_message: str, extracted: ExtractedSymptoms) -> BuiltPrompt:
        """
        Original single-turn prompt builder.
        Kept identical to v1 — no callers need updating.
        What it does:

        Combine the fixed system prompt with a context-enriched user prompt.

        Args:
            user_message: The raw text from the user.
            extracted:    Structured data from SymptomExtractor.

        Returns:
            BuiltPrompt with `system_prompt` and `user_prompt` fields.
        """
        system = self._build_system_prompt(extracted)
        user   = self._build_user_prompt(user_message, extracted)
        return BuiltPrompt(system_prompt=system, user_prompt=user)

    # ── v2 method — NEW ───────────────────────────────────────────

    def build_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      "list[Message]",
    ) -> BuiltPrompt:
        """
        Multi-turn prompt builder that weaves conversation history
        into the user prompt.

        Prompt structure sent to the LLM:

            [system]
            You are Arogya AI …

            [user]
            Conversation so far:
            User: <oldest message>
            Assistant: <reply>
            User: <next message>
            Assistant: <reply>
            …

            Current message:
            User: <new message>

            [Structured symptom context if available]

        Args:
            user_message: The new message just typed by the user.
            extracted:    Structured output from SymptomExtractor.
            history:      Past messages from MemoryStore, oldest first.
                          This list should NOT include the current message —
                          it is appended here explicitly.
        """
        system      = self._build_system_prompt(extracted)
        user_prompt = self._build_user_prompt_with_history(
            user_message, extracted, history
        )
        return BuiltPrompt(system_prompt=system, user_prompt=user_prompt)

    # ── Private helpers ───────────────────────────────────────────

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

        return self._symptom_context(extracted) + user_message

    def _build_user_prompt_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      "list[Message]",
    ) -> str:
        """
        Construct the full user-turn content for a multi-turn conversation.

        Layout:
            Conversation so far:     ← only present when history is non-empty
            User: …
            Assistant: …
            …

            Current message:
            User: <user_message>

            [symptom context block]  ← only present when symptoms detected
        """
        parts: list[str] = []

        # ── Section 1: conversation history ──────────────────────
        if history:
            parts.append("Conversation so far:")
            parts.append(self._format_history(history))
            parts.append("")   # blank line before "Current message"

        # ── Section 2: current user message ──────────────────────
        parts.append("Current message:")
        parts.append(f"User: {user_message}")

        # ── Section 3: structured symptom context ────────────────
        if extracted.symptoms or extracted.duration:
            parts.append("")
            parts.append(self._symptom_context(extracted).strip())

        return "\n".join(parts)

    def _format_history(self, history: "list[Message]") -> str:
        """
        Convert a list of Message objects into a readable dialogue block.

        Example output:
            User: I have had a cough for two days.
            Assistant: I understand you're experiencing a cough …
            User: Should I be worried?
            Assistant: A cough lasting two days is often …
        """
        lines: list[str] = []
        for msg in history:
            # Capitalise role label: "user" → "User", "assistant" → "Assistant"
            label = msg.role.capitalize()
            lines.append(f"{label}: {msg.content}")
        return "\n".join(lines)

    def _symptom_context(self, extracted: ExtractedSymptoms) -> str:
        """Format the structured symptom context block."""
        return _SYMPTOM_CONTEXT_TEMPLATE.format(
            symptoms   = ", ".join(extracted.symptoms)    if extracted.symptoms    else "not specified",
            duration   = extracted.duration               if extracted.duration    else "not mentioned",
            body_parts = ", ".join(extracted.body_parts)  if extracted.body_parts  else "not mentioned",
            severity   = ", ".join(extracted.severity_hints) if extracted.severity_hints else "not mentioned",
        )
