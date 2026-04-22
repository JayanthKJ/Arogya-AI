"""
services/prompt_builder.py  (v10 — decision-driven, minimal, non-redundant)
-----------------------------------------------------------------------------
Builds the system and user prompts sent to the LLM.

Pipeline context:
  User → Extractor → Interpreter → Decision Layer → PromptBuilder → LLM

CHANGE LOG (v10):
  - build_with_history() fully rewritten: minimal, structured, decision-aware
  - Added _build_health_state() helper — renders interpreted context cleanly
  - Added _build_response_strategy() helper — maps decision type to behavior
  - Removed all redundancy: extracted symptoms suppressed when interpreted exists
  - _build_system_prompt(), build(), _build_user_prompt() UNCHANGED
"""

from __future__ import annotations

from models.schemas import ExtractedSymptoms, BuiltPrompt

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from services.memory_store import Message


# ── System prompt (unchanged) ─────────────────────────────────────────────────

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
10. Focus on the emergency contacts based in India if any serious symptoms show up.
11. Use very simple and everyday English.
12. Avoid medical or complex words.
13. Speak like you are talking to a normal person, not a doctor.
14. Use short sentences.
15. Prefer common words: say "doctor" instead of "healthcare professional", say "get help fast" instead of "seek immediate medical attention".
16. Be warm, calm, and reassuring.
17. Do not sound robotic or overly formal.
18. Assume the user may not be fluent in English. Write so that even a 10-year-old can understand.
19. Do NOT ask too many questions.
20. Ask at most ONE follow-up question per response.
21. Only ask a question if it is truly necessary to help the user.
22. If the user message is already clear, do NOT ask any questions.
23. Make questions optional and gentle, not forceful.
24. Use soft phrasing like: "If you want, you can tell me...", "You can also share...", "If it helps, you can mention...".
25. Do NOT ask multiple questions in a row.
26. Avoid sounding like an interrogation.
27. Always provide helpful guidance or suggestions in every response.
28. Do NOT respond with only a question.
29. A question can be included only AFTER giving useful information.
30. The primary goal is to help the user, not to ask questions.
31. If you ask a question, limit it to ONE and make it optional."""

# ── Symptom context block — used by legacy build() only ──────────────────────

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

# ── Emergency symptoms (unchanged) ───────────────────────────────────────────

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
      build()              — single-turn (no history), legacy behaviour.
      build_with_history() — multi-turn, decision-driven prompt construction.
    """

    # ── v10: decision-driven multi-turn method ────────────────────────────────

    def build_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      list[dict],
        interpreted:  dict | None = None,
        decision:     dict | None = None,
    ) -> BuiltPrompt:
        """
        Build a minimal, structured, decision-aware prompt.

        User prompt structure:
        ┌──────────────────────────────────────┐
        │  1. Conversation History (if any)    │
        │  2. Current Message                  │
        │  3. Health State (from interpreted)  │
        │  4. Response Strategy (from decision)│
        └──────────────────────────────────────┘
        """
        system = self._build_system_prompt(extracted)
        user   = self._build_user_prompt_with_history(
            user_message, extracted, history, interpreted, decision
        )
        return BuiltPrompt(system_prompt=system, user_prompt=user)

    def _build_user_prompt_with_history(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      list[dict],
        interpreted:  dict | None = None,
        decision:     dict | None = None,
    ) -> str:
        """
        Assemble the full user-facing prompt string across six sections.
        """
        parts: list[str] = []

        # ── Section 1: conversation history ──────────────────────
        if history:
            parts.append("[Conversation History]")
            for turn in history:
                label = turn["role"].capitalize()
                parts.append(f"{label}: {turn['content']}")
            parts.append("")
            parts.append("Analyze how the user's condition has evolved across the conversation before responding.")

        # ── Section 2: current message ───────────────────────────
        parts.append("[Current Message]")
        parts.append(f"User: {user_message}")
        parts.append("")

        # ── Section 3: health state ───────────────────────────────
        # If interpreted exists → use it exclusively (no extracted duplication).
        # If not → fall back to raw extracted symptoms only.
        parts.append(self._build_health_state(extracted, interpreted))

        # ── Section 4: response strategy ─────────────────────────
        parts.append(self._build_response_strategy(decision))

        return "\n".join(parts)

    # ── Helper: health state ──────────────────────────────────────────────────

    def _build_health_state(
        self,
        extracted:   ExtractedSymptoms,
        interpreted: dict | None,
    ) -> str:
        """
        Render the health state block.
        Uses interpreted output when available — never duplicates with extracted.
        Falls back to raw extracted symptoms only when interpreter is unavailable.
        """
        lines: list[str] = ["[Health State]"]

        if interpreted and isinstance(interpreted, dict):
            # Interpreted is the primary source — extracted is NOT repeated
            symptoms_str = ", ".join(interpreted["symptoms"]) if interpreted["symptoms"] else "none mentioned"
            lines.append(f"- symptoms : {symptoms_str}")
            lines.append(f"- trend    : {interpreted.get('trend', 'unknown')}")
            lines.append(f"- severity : {interpreted.get('severity', 'unknown')}")
            lines.append(f"- duration : {interpreted.get('duration', 'unknown')}")
        else:
            # Interpreter unavailable — use raw extracted symptoms as minimal fallback
            if extracted.symptoms:
                lines.append(f"- symptoms : {', '.join(extracted.symptoms)}")
            else:
                lines.append("- symptoms : not detected")
            lines.append("- trend    : unknown")
            lines.append("- severity : unknown")
            lines.append("- duration : unknown")

        return "\n".join(lines)

    # ── Helper: response strategy ─────────────────────────────────────────────

    def _build_response_strategy(self, decision: dict | None) -> str:
        """
        Map the decision type to strict, directive LLM behavior instructions.
        This is the primary driver of response variation.
        """
        lines: list[str] = ["", "[Response Strategy]"]
        lines.append("You MUST follow this strategy while generating the response.")
        lines.append("")

        # ── Conversation Awareness — injected before all decision types ──────────
        lines.append("[Conversation Awareness]")
        lines.append("- Compare the user's current condition with what they said in earlier messages.")
        lines.append("- If the condition has worsened, explicitly mention the change.")
        lines.append("  Example: \"Earlier you mentioned it was getting worse — now it sounds even more severe.\"")
        lines.append("- Do NOT just repeat the user's words back to them.")
        lines.append("- Show that you understand how things have progressed.")
        lines.append("- Do NOT repeat questions already asked in this conversation.")
        lines.append("- If the user answered a question earlier, acknowledge that naturally.")
        lines.append("")

        decision_type = decision.get("type", "respond") if decision else "respond"

        if decision_type == "ask":
            lines.append("type: ask")
            lines.append("Follow this order strictly:")
            lines.append("1. Ask 1 or 2 specific clarifying questions.")
            lines.append("2. Do NOT give full advice.")
            lines.append("3. Do NOT assume any symptoms.")
            lines.append("Rules:")
            lines.append("- Ask at most 2 questions.")
            lines.append("- Keep questions short and clear.")

        elif decision_type == "caution":
            lines.append("type: caution")
            lines.append("Follow this order strictly:")
            lines.append("1. First, clearly acknowledge that the condition is getting worse.")
            lines.append("2. Then briefly explain why this matters.")
            lines.append("3. Then give ONLY 1-2 simple actions.")
            lines.append("4. Then suggest seeing a doctor if needed.")
            lines.append("5. Optionally ask ONE short question at the end.")
            lines.append("Rules:")
            lines.append("- Do NOT give long explanations.")
            lines.append("- Do NOT ask more than one question.")

        elif decision_type == "escalate":
            lines.append("type: escalate")
            lines.append("Follow this order strictly:")
            lines.append("1. Start with a clear and urgent warning.")
            lines.append("2. Strongly advise the user to get medical help immediately.")
            lines.append("Rules:")
            lines.append("- DO NOT ask any questions.")
            lines.append("- DO NOT give general explanations or casual suggestions.")
            lines.append("- Keep the response short and serious.")

        else:   # "respond" — default
            lines.append("type: respond")
            lines.append("Follow this order strictly:")
            lines.append("1. Acknowledge the user's current condition simply.")
            lines.append("2. Give a clear and simple explanation.")
            lines.append("3. Provide 1-2 helpful suggestions.")
            lines.append("Rules:")
            lines.append("- No unnecessary questions.")
            lines.append("- Keep the tone calm and easy to understand.")
            lines.append("- Avoid long explanations.")

        return "\n".join(lines)

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