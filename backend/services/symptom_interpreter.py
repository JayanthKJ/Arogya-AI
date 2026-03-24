"""
services/symptom_interpreter.py
--------------------------------
Rule-based interpreter that builds a structured health context
from the current message, extracted symptoms, and conversation history.

Returns a fixed-shape dict — no ML, no external APIs, no diagnosis.
"""

import re
from models.schemas import ExtractedSymptoms
from services.memory_store import Message


# ── Normalization map ─────────────────────────────────────────────────────────
# Maps vague user phrases → canonical symptom names.

_NORMALIZATION_MAP: dict[str, str] = {
    "cold":         "chills",
    "chilling":     "chills",
    "weak":         "fatigue",
    "weakness":     "fatigue",
    "tired":        "fatigue",
    "heavy head":   "headache",
    "head is heavy":"headache",
    "body pain":    "muscle ache",
    "body ache":    "muscle ache",
    "stomach ache": "stomach pain",
    "tummy ache":   "stomach pain",
    "throwing up":  "vomiting",
    "threw up":     "vomiting",
    "can't breathe":"shortness of breath",
    "hard to breathe":"shortness of breath",
    "feeling hot":  "fever",
    "running nose": "runny nose",
    "loose motion": "diarrhea",
    "loose stools": "diarrhea",
    "chest tight":  "chest tightness",
    "heart racing": "palpitations",
    "can't sleep":  "insomnia",
    "no appetite":  "loss of appetite",
    "not eating":   "loss of appetite",
}

# ── Trend keywords ────────────────────────────────────────────────────────────

_WORSENING_WORDS = {"worse", "worsening", "intense", "intensifying", "increasing",
                    "more", "getting bad", "getting worse", "severe now", "unbearable now"}

_IMPROVING_WORDS = {"better", "improving", "improved", "less", "reduced",
                    "reducing", "easing", "eased", "getting better", "feeling better"}

_SAME_WORDS      = {"same", "still", "unchanged", "no change", "as before",
                    "not better", "not worse"}

# ── Severity keywords ─────────────────────────────────────────────────────────

_MILD_WORDS     = {"slight", "little", "mild", "minor", "light", "faint", "barely"}

_MODERATE_WORDS = {"moderate", "noticeable", "intense", "considerable", "significant",
                   "annoying", "bothering"}

_SEVERE_WORDS   = {"severe", "very bad", "extreme", "unbearable", "terrible",
                   "excruciating", "worst", "horrible", "can't bear", "emergency"}


# ── SymptomInterpreter ────────────────────────────────────────────────────────

class SymptomInterpreter:
    """
    Stateless interpreter — instantiate once and reuse.

    Usage:
        interpreter = SymptomInterpreter()
        result = interpreter.interpret(user_message, extracted, history)
    """

    def interpret(
        self,
        user_message: str,
        extracted:    ExtractedSymptoms,
        history:      list[Message],
    ) -> dict:
        """
        Build a structured health context dictionary.

        Args:
            user_message: Raw text from the user.
            extracted:    Output of SymptomExtractor.
            history:      Prior conversation turns from MemoryStore.

        Returns:
            {
              "symptoms": list[str],
              "severity": "mild" | "moderate" | "severe" | "unknown",
              "trend":    "new" | "same" | "worsening" | "improving" | "unknown",
              "duration": "short" | "ongoing" | "unknown",
              "confidence": "low" | "medium" | "high",
            }
        """
        lower = user_message.lower()

        symptoms = self._resolve_symptoms(lower, extracted)
        severity = self._detect_severity(lower)
        trend    = self._detect_trend(lower, history)
        duration = self._resolve_duration(extracted, history)
        confidence = self._score_confidence(symptoms, trend)

        return {
            "symptoms":   symptoms,
            "severity":   severity,
            "trend":      trend,
            "duration":   duration,
            "confidence": confidence,
        }

    # ── 1. Symptom normalization ──────────────────────────────────

    def _resolve_symptoms(self, text: str, extracted: ExtractedSymptoms) -> list[str]:
        """
        Use extracted symptoms if available.
        Otherwise, scan the message against the normalization map.
        Deduplicate while preserving order.
        """
        if extracted.symptoms:
            return list(extracted.symptoms)

        # Fallback: try to infer from vague phrasing
        inferred: list[str] = []
        for phrase, canonical in _NORMALIZATION_MAP.items():
            if phrase in text and canonical not in inferred:
                inferred.append(canonical)

        return inferred

    # ── 2. Trend detection ────────────────────────────────────────

    def _detect_trend(self, text: str, history: list[Message]) -> str:
        """
        Determine whether symptoms are new, worsening, improving, or unchanged.
        Checks current message first, then falls back to history presence.
        """
        # Check current message for trend keywords
        if self._matches_any(text, _WORSENING_WORDS):
            return "worsening"
        if self._matches_any(text, _IMPROVING_WORDS):
            return "improving"
        if self._matches_any(text, _SAME_WORDS):
            return "same"

        # No trend keywords — if there's history, this is a continuation
        if history:
            return "same"

        # No history and no keywords — this is a fresh complaint
        return "new"

    # ── 3. Severity detection ─────────────────────────────────────

    def _detect_severity(self, text: str) -> str:
        """
        Map severity keywords in the message to a severity level.
        Checks severe first (most specific), then moderate, then mild.
        """
        if self._matches_any(text, _SEVERE_WORDS):
            return "severe"
        if self._matches_any(text, _MODERATE_WORDS):
            return "moderate"
        if self._matches_any(text, _MILD_WORDS):
            return "mild"
        return "unknown"

    # ── 4. Duration resolution ────────────────────────────────────

    def _resolve_duration(self, extracted: ExtractedSymptoms, history: list[Message]) -> str:
        """
        Classify duration as short, ongoing, or unknown.
        Uses structured duration from extractor when available.
        Falls back to history presence.
        """
        if extracted.duration:
            # Any explicitly mentioned duration = the symptom has a known timeframe
            return "short" if self._is_short_duration(extracted.duration) else "ongoing"

        # No duration mentioned — infer from whether there's prior history
        if history:
            return "ongoing"

        return "unknown"

    # ── 5. Confidence scoring ─────────────────────────────────────

    def _score_confidence(self, symptoms: list[str], trend: str) -> str:
        """
        Estimate how much structured data was successfully extracted.
          high   → symptoms found AND trend is known
          medium → symptoms found but trend is unknown/new
          low    → little or nothing detected
        """
        has_symptoms = len(symptoms) > 0
        has_trend    = trend not in ("unknown", "new")

        if has_symptoms and has_trend:
            return "high"
        if has_symptoms:
            return "medium"
        return "low"

    # ── Helpers ───────────────────────────────────────────────────

    def _matches_any(self, text: str, keywords: set[str]) -> bool:
        """Return True if any keyword from the set appears in text."""
        return any(kw in text for kw in keywords)

    def _is_short_duration(self, duration_str: str) -> bool:
        """
        Return True if the duration string suggests a short timeframe
        (hours or 1-3 days). Everything else is considered ongoing.
        """
        short_patterns = [
            r"\b\d+\s*(?:hr|hrs|hour|hours|min|mins|minute|minutes)\b",
            r"\b[1-3]\s*day[s]?\b",
            r"\ba\s*day\b",
        ]
        lower = duration_str.lower()
        return any(re.search(p, lower) for p in short_patterns)