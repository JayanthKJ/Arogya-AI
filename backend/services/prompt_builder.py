"""
services/prompt_builder.py
---------------------------
Builds the system and user prompts that are sent to the LLM.

Responsibilities:
  1. Define Arogya AI's identity, tone, and safety boundaries.
  2. Enrich the user prompt with the structured symptom context so the
     LLM can give more relevant guidance without needing to re-parse text.
  3. Keep the system prompt short and direct — LLMs follow concise
     instructions more reliably than long paragraphs.
"""

from models.schemas import ExtractedSymptoms, BuiltPrompt

# ── System prompt template ────────────────────────────────────────────────────
# This is the "persona" injected at the top of every LLM conversation.
# It is intentionally conservative to keep the AI within safe bounds.

_SYSTEM_PROMPT = """You are Arogya AI, a compassionate and knowledgeable health guidance assistant designed to help people understand their health better.

YOUR CORE PRINCIPLES:
1. NEVER provide a medical diagnosis or claim to diagnose any condition.
2. NEVER prescribe, recommend, or name specific medications or dosages.
3. ALWAYS remind users to consult a qualified doctor for any serious, persistent, or worsening symptoms.
4. Provide clear, simple, general health information and lifestyle guidance only.
5. Use warm, respectful, easy-to-understand language suitable for all ages.
6. If symptoms sound potentially serious (chest pain, difficulty breathing, stroke signs, etc.), advise the user to seek emergency care immediately.
7. Keep responses concise: 3–5 short paragraphs maximum.
8. End every response with a doctor-consultation reminder unless the user is asking a trivially general question."""

# ── Symptom context template ──────────────────────────────────────────────────
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

# ── Emergency symptom keywords (trigger extra-urgent advice) ─────────────────
_EMERGENCY_SYMPTOMS = {
    "chest pain", "chest tightness", "difficulty breathing",
    "shortness of breath", "stroke", "paralysis", "unconscious",
    "fainting", "seizure", "severe bleeding", "coughing blood",
    "blood in stool", "sudden vision loss",
}


class PromptBuilder:
    """
    Stateless builder — instantiate once and reuse.

    Usage:
        builder = PromptBuilder()
        prompt = builder.build(user_message, extracted_symptoms)
        # BuiltPrompt(system_prompt="...", user_prompt="...")
    """

    def build(self, user_message: str, extracted: ExtractedSymptoms) -> BuiltPrompt:
        """
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

    # ── Private helpers ───────────────────────────────────────────

    def _build_system_prompt(self, extracted: ExtractedSymptoms) -> str:
        """
        Append an emergency notice to the base system prompt when
        potentially urgent symptoms are detected.
        """
        system = _SYSTEM_PROMPT

        # Check whether any extracted symptom is flagged as emergency
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
        If symptoms were detected, prepend structured context so the LLM
        has clean, parsed data alongside the original free-text message.
        If nothing was extracted, just pass the message through.
        """
        if not extracted.symptoms and not extracted.duration:
            # No structured data — send as-is
            return user_message

        # Format each field, falling back to a human-readable "not mentioned"
        symptoms_str   = ", ".join(extracted.symptoms)  if extracted.symptoms    else "not specified"
        duration_str   = extracted.duration              if extracted.duration    else "not mentioned"
        body_parts_str = ", ".join(extracted.body_parts) if extracted.body_parts  else "not mentioned"
        severity_str   = ", ".join(extracted.severity_hints) if extracted.severity_hints else "not mentioned"

        context = _SYMPTOM_CONTEXT_TEMPLATE.format(
            symptoms=symptoms_str,
            duration=duration_str,
            body_parts=body_parts_str,
            severity=severity_str,
        )

        return context + user_message
