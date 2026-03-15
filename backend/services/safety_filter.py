"""
services/safety_filter.py
--------------------------
Post-processes the LLM's raw reply before it is sent to the user.

Two-stage approach:
  1. Hard block  — phrases that can NEVER appear in a health AI response.
                   If detected, the entire reply is replaced with a safe fallback.
  2. Soft rewrite — patterns that are problematic but can be safely rewritten
                   in-place (e.g. "you have X" → "it sounds like you may be
                   experiencing X").

This runs after the LLM call so it acts as a safety net regardless of
what the model produces.
"""

import re
from dataclasses import dataclass

# ── Hard-block phrases ────────────────────────────────────────────────────────
# If ANY of these appear in the response (case-insensitive), the reply is
# discarded and replaced with the generic safe fallback below.

_HARD_BLOCK_PHRASES: list[str] = [
    # Diagnosis claims
    "you definitely have",
    "you are diagnosed with",
    "you have been diagnosed",
    "you are suffering from",        # too certain; "may be" is safer
    "the diagnosis is",
    "you have [a-z]+ disease",       # regex: "you have diabetes"
    "you have [a-z]+ cancer",

    # Medication prescription
    "take this medicine",
    "take this medication",
    "you should take",
    "i recommend taking",
    "i prescribe",
    "the prescription is",
    "dosage is",
    "take \\d+\\s*mg",               # regex: "take 500mg"
    "take \\d+\\s*tablet",

    # Dangerous certainty
    "this is definitely",
    "this is certainly",
    "100% sure",
    "no need to see a doctor",
    "you don't need a doctor",
    "do not go to the hospital",
]

# ── Soft-rewrite rules ────────────────────────────────────────────────────────
# List of (pattern, replacement) tuples applied via re.sub.
# These tone down overly confident language without replacing the whole reply.

_SOFT_REWRITES: list[tuple[str, str]] = [
    # "you have X" → "you may be experiencing X"
    (
        r"\byou have\b(?! a doctor| been| already| always| any)",
        "you may be experiencing",
    ),
    # "This is X disease/condition" → "This could be related to X"
    (
        r"\bthis is\s+(a\s+)?([a-z]+ (?:disease|condition|infection|disorder))\b",
        r"this could be related to \2",
    ),
    # "It is X" at sentence start (e.g. "It is viral fever") → "It may be"
    (
        r"\bIt is\b(?! important| best| recommended| a good)",
        "It may be",
    ),
    # Remove em-dashes followed by drug names pattern (crude but catches common cases)
    (
        r"\b(paracetamol|ibuprofen|aspirin|amoxicillin|metformin|atorvastatin)\b",
        "[medication name omitted — please ask your doctor]",
    ),
]

# ── Safe fallback response ────────────────────────────────────────────────────
_SAFE_FALLBACK = (
    "I'm not able to provide a specific assessment for your situation. "
    "Your symptoms could have various causes and it's important to have "
    "them properly evaluated by a qualified healthcare professional.\n\n"
    "Please consider:\n"
    "• Visiting your nearest clinic or hospital\n"
    "• Calling your doctor or a nurse helpline\n"
    "• Going to an emergency room if symptoms are severe or worsening\n\n"
    "I'm here to provide general health information, but your doctor is "
    "the right person to diagnose and treat your specific condition. "
    "Please don't delay seeking medical help."
)


@dataclass
class FilterResult:
    """Carries the final reply and a flag indicating whether it was modified."""
    reply: str
    was_modified: bool   # True if hard-blocked or soft-rewritten


class SafetyFilter:
    """
    Stateless filter — instantiate once and reuse.

    Usage:
        sf = SafetyFilter()
        result = sf.filter("You definitely have diabetes. Take Metformin.")
        # result.reply        → safe fallback text
        # result.was_modified → True
    """

    def __init__(self) -> None:
        # Pre-compile all patterns for performance
        self._hard_patterns = [
            re.compile(p, re.IGNORECASE) for p in _HARD_BLOCK_PHRASES
        ]
        self._soft_patterns = [
            (re.compile(p, re.IGNORECASE), r) for p, r in _SOFT_REWRITES
        ]

    # ── Public API ────────────────────────────────────────────────

    def filter(self, raw_reply: str) -> FilterResult:
        """
        Apply hard-block check first, then soft rewrites.

        Args:
            raw_reply: The text returned directly by the LLM.

        Returns:
            FilterResult with the cleaned reply and a modification flag.
        """
        # Stage 1 — hard block
        if self._is_hard_blocked(raw_reply):
            return FilterResult(reply=_SAFE_FALLBACK, was_modified=True)

        # Stage 2 — soft rewrites
        cleaned, changed = self._apply_soft_rewrites(raw_reply)

        return FilterResult(reply=cleaned, was_modified=changed)

    # ── Private helpers ───────────────────────────────────────────

    def _is_hard_blocked(self, text: str) -> bool:
        """Return True if any hard-block pattern is found in `text`."""
        return any(pattern.search(text) for pattern in self._hard_patterns)

    def _apply_soft_rewrites(self, text: str) -> tuple[str, bool]:
        """
        Apply all soft-rewrite rules in sequence.
        Returns the rewritten text and whether any substitution was made.
        """
        result = text
        changed = False
        for pattern, replacement in self._soft_patterns:
            new_result = pattern.sub(replacement, result)
            if new_result != result:
                changed = True
                result = new_result
        return result, changed
