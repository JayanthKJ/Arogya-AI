"""
services/symptom_extractor.py
------------------------------
Lightweight, rule-based symptom extractor.
Parses the user's free-text message to surface:
  - symptoms      (fever, cough, headache …)
  - duration      ("3 days", "since yesterday" …)
  - body parts    (chest, stomach, back …)
  - severity hints (mild, severe, unbearable …)

Intentionally dependency-free (no ML model required) so it works
immediately without GPU or large downloads.  A spaCy/NER-based version
can replace this class without changing its interface.
"""

import re
from models.schemas import ExtractedSymptoms

# ── Symptom vocabulary ────────────────────────────────────────────────────────
# Extend this list as the product grows.  Keys are canonical names.

KNOWN_SYMPTOMS: list[str] = [
    # General
    "fever", "chills", "fatigue", "weakness", "tiredness", "malaise",
    "night sweats", "weight loss", "weight gain",
    # Head / neuro
    "headache", "migraine", "dizziness", "vertigo", "confusion",
    "memory loss", "fainting", "seizure",
    # Eyes / ears / nose / throat
    "blurred vision", "eye pain", "ear pain", "hearing loss",
    "runny nose", "stuffy nose", "nasal congestion", "sneezing",
    "sore throat", "hoarseness", "difficulty swallowing",
    # Respiratory
    "cough", "dry cough", "wet cough", "shortness of breath",
    "wheezing", "chest tightness", "chest pain",
    # Cardiac
    "palpitations", "irregular heartbeat", "rapid heartbeat",
    # GI
    "nausea", "vomiting", "diarrhea", "constipation", "bloating",
    "abdominal pain", "stomach pain", "stomach ache", "indigestion",
    "heartburn", "loss of appetite",
    # Musculoskeletal
    "joint pain", "muscle pain", "back pain", "neck pain",
    "knee pain", "shoulder pain", "body ache", "stiffness",
    # Skin
    "rash", "itching", "hives", "swelling", "redness", "bruising",
    # Urinary
    "frequent urination", "painful urination", "blood in urine",
    # Other
    "anxiety", "depression", "insomnia", "sleep problems",
]

# ── Duration patterns ─────────────────────────────────────────────────────────
# Matches expressions like "3 days", "two weeks", "since yesterday", "for a month"
_DURATION_PATTERNS: list[str] = [
    r"\bfor\s+(?:the\s+)?(?:past\s+)?(\d+\s+(?:day|days|week|weeks|month|months|hour|hours|year|years|min|mins|minute|minutes))\b",
    r"\b(\d+\s+(?:day|days|week|weeks|month|months|hour|hours|year|years|min|mins|minute|minutes))\b",
    r"\b(since\s+(?:yesterday|last\s+\w+|this\s+\w+|\w+\s+days?\s+ago))\b",
    r"\b(since\s+\d+\s+(?:day|days|week|weeks|month|months))\b",
    r"\b(from\s+(?:yesterday|last\s+\w+))\b",
    r"\b(a\s+(?:day|week|month|few\s+days|couple\s+of\s+days))\b",
]

# ── Body part vocabulary ──────────────────────────────────────────────────────
BODY_PARTS: list[str] = [
    "head", "eye", "eyes", "ear", "ears", "nose", "throat", "neck",
    "chest", "back", "shoulder", "arm", "elbow", "wrist", "hand",
    "stomach", "abdomen", "hip", "leg", "knee", "ankle", "foot",
    "skin", "liver", "kidney", "heart", "lung", "lungs",
]

# ── Severity vocabulary ───────────────────────────────────────────────────────
SEVERITY_WORDS: list[str] = [
    "mild", "moderate", "severe", "extreme", "unbearable",
    "sharp", "dull", "constant", "intermittent", "sudden",
    "persistent", "chronic", "acute", "recurring",
]


class SymptomExtractor:
    """
    Stateless extractor — instantiate once and reuse.

    Usage:
        extractor = SymptomExtractor()
        result = extractor.extract("I have fever and headache for 3 days")
        # ExtractedSymptoms(symptoms=["fever","headache"], duration="3 days", ...)
    """

    def __init__(self) -> None:
        # Pre-compile duration regexes for performance
        self._duration_re = [
            re.compile(p, re.IGNORECASE) for p in _DURATION_PATTERNS
        ]

    # ── Public API ────────────────────────────────────────────────

    def extract(self, text: str) -> ExtractedSymptoms:
        """
        Parse `text` and return a structured ExtractedSymptoms object.
        All matching is case-insensitive.
        """
        lower = text.lower()

        symptoms      = self._extract_symptoms(lower)
        duration      = self._extract_duration(lower)
        body_parts    = self._extract_body_parts(lower)
        severity_hints = self._extract_severity(lower)

        return ExtractedSymptoms(
            symptoms=symptoms,
            duration=duration,
            body_parts=body_parts,
            severity_hints=severity_hints,
        )

    # ── Private helpers ───────────────────────────────────────────

    def _extract_symptoms(self, text: str) -> list[str]:
        """Return all known symptoms found in `text`, preserving order."""
        found: list[str] = []
        for symptom in KNOWN_SYMPTOMS:
            # Word-boundary match to avoid partial hits (e.g. "pain" inside "explain")
            pattern = r"\b" + re.escape(symptom) + r"\b"
            if re.search(pattern, text):
                found.append(symptom)
        return found

    def _extract_duration(self, text: str) -> str | None:
        """Return the first duration expression found, or None."""
        for regex in self._duration_re:
            match = regex.search(text)
            if match:
                # Return the first capturing group, stripped
                return match.group(1).strip()
        return None

    def _extract_body_parts(self, text: str) -> list[str]:
        """Return all body-part words found in `text`."""
        found: list[str] = []
        for part in BODY_PARTS:
            if re.search(r"\b" + re.escape(part) + r"\b", text):
                found.append(part)
        return found

    def _extract_severity(self, text: str) -> list[str]:
        """Return all severity-hint words found in `text`."""
        found: list[str] = []
        for word in SEVERITY_WORDS:
            if re.search(r"\b" + re.escape(word) + r"\b", text):
                found.append(word)
        return found
