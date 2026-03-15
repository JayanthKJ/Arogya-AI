"""
tests/test_backend.py
---------------------
Unit and integration tests for all backend layers.

Run:
    pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

# ── Ensure the app can be imported from the backend root ──────────
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from services.symptom_extractor import SymptomExtractor
from services.prompt_builder    import PromptBuilder
from services.safety_filter     import SafetyFilter
from models.schemas             import ExtractedSymptoms


# ═══════════════════════════════════════════════════════════════════
# SymptomExtractor
# ═══════════════════════════════════════════════════════════════════

class TestSymptomExtractor:
    extractor = SymptomExtractor()

    def test_basic_symptoms(self):
        result = self.extractor.extract("I have fever and headache for 3 days")
        assert "fever"    in result.symptoms
        assert "headache" in result.symptoms

    def test_duration_days(self):
        result = self.extractor.extract("I have fever and headache for 3 days")
        assert result.duration == "3 days"

    def test_duration_weeks(self):
        result = self.extractor.extract("I have had a cough for 2 weeks")
        assert result.duration == "2 weeks"

    def test_duration_since_yesterday(self):
        result = self.extractor.extract("I have had chest pain since yesterday")
        assert result.duration is not None
        assert "yesterday" in result.duration.lower()

    def test_no_duration(self):
        result = self.extractor.extract("My head hurts")
        assert result.duration is None

    def test_body_parts(self):
        result = self.extractor.extract("I have pain in my chest and back")
        assert "chest" in result.body_parts
        assert "back"  in result.body_parts

    def test_severity(self):
        result = self.extractor.extract("I have severe chest pain")
        assert "severe" in result.severity_hints

    def test_empty_message(self):
        result = self.extractor.extract("Hello, how are you?")
        assert result.symptoms == []
        assert result.duration is None

    def test_multiple_symptoms(self):
        result = self.extractor.extract(
            "I have nausea, vomiting, and diarrhea since yesterday"
        )
        assert "nausea"    in result.symptoms
        assert "vomiting"  in result.symptoms
        assert "diarrhea"  in result.symptoms


# ═══════════════════════════════════════════════════════════════════
# PromptBuilder
# ═══════════════════════════════════════════════════════════════════

class TestPromptBuilder:
    builder = PromptBuilder()

    def _extracted(self, symptoms=None, duration=None):
        return ExtractedSymptoms(
            symptoms=symptoms or [],
            duration=duration,
        )

    def test_system_prompt_contains_identity(self):
        ext = self._extracted()
        prompt = self.builder.build("hello", ext)
        assert "Arogya AI" in prompt.system_prompt

    def test_system_prompt_contains_safety_rules(self):
        ext = self._extracted()
        prompt = self.builder.build("hello", ext)
        assert "diagnosis" in prompt.system_prompt.lower()
        assert "prescribe" in prompt.system_prompt.lower() or "medication" in prompt.system_prompt.lower()

    def test_user_prompt_includes_symptoms(self):
        ext = self._extracted(symptoms=["fever", "cough"], duration="2 days")
        prompt = self.builder.build("I feel sick", ext)
        assert "fever" in prompt.user_prompt
        assert "2 days" in prompt.user_prompt

    def test_no_symptoms_passes_message_through(self):
        ext = self._extracted()
        prompt = self.builder.build("What foods are healthy?", ext)
        assert "What foods are healthy?" in prompt.user_prompt

    def test_emergency_symptom_adds_critical_notice(self):
        ext = self._extracted(symptoms=["chest pain"])
        prompt = self.builder.build("I have chest pain", ext)
        assert "CRITICAL" in prompt.system_prompt or "emergency" in prompt.system_prompt.lower()


# ═══════════════════════════════════════════════════════════════════
# SafetyFilter
# ═══════════════════════════════════════════════════════════════════

class TestSafetyFilter:
    sf = SafetyFilter()

    def test_safe_text_unchanged(self):
        text = "Please consult your doctor for proper guidance on your symptoms."
        result = self.sf.filter(text)
        assert result.reply == text
        assert result.was_modified is False

    def test_hard_block_diagnosis(self):
        text = "You definitely have diabetes and should start insulin immediately."
        result = self.sf.filter(text)
        assert result.was_modified is True
        assert "You definitely have" not in result.reply

    def test_hard_block_prescription(self):
        text = "Take this medicine twice a day for a week."
        result = self.sf.filter(text)
        assert result.was_modified is True

    def test_hard_block_diagnosed_with(self):
        text = "You are diagnosed with hypertension."
        result = self.sf.filter(text)
        assert result.was_modified is True

    def test_soft_rewrite_you_have(self):
        text = "It seems you have a viral infection based on your symptoms."
        result = self.sf.filter(text)
        # "you have" should be softened
        assert "you definitely have" not in result.reply.lower()

    def test_hard_block_returns_fallback(self):
        text = "You definitely have cancer. Take this medicine immediately."
        result = self.sf.filter(text)
        assert result.was_modified is True
        assert "doctor" in result.reply.lower()

    def test_no_need_to_see_doctor(self):
        text = "You don't need a doctor, just rest at home."
        result = self.sf.filter(text)
        assert result.was_modified is True


# ═══════════════════════════════════════════════════════════════════
# Chat Route (integration)
# ═══════════════════════════════════════════════════════════════════

class TestChatRoute:
    client = TestClient(app)

    def test_health_check(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_chat_valid_message(self):
        r = self.client.post("/chat/", json={"message": "I have fever for 2 days"})
        assert r.status_code == 200
        body = r.json()
        assert "reply"     in body
        assert "extracted" in body
        assert "safe"      in body
        assert len(body["reply"]) > 0

    def test_chat_extracts_symptoms(self):
        r = self.client.post("/chat/", json={"message": "I have headache and nausea"})
        assert r.status_code == 200
        extracted = r.json()["extracted"]
        assert "headache" in extracted["symptoms"]
        assert "nausea"   in extracted["symptoms"]

    def test_chat_empty_message_rejected(self):
        r = self.client.post("/chat/", json={"message": ""})
        assert r.status_code == 422   # Pydantic validation error

    def test_chat_whitespace_message_rejected(self):
        r = self.client.post("/chat/", json={"message": "   "})
        assert r.status_code == 422

    def test_chat_missing_message_field(self):
        r = self.client.post("/chat/", json={})
        assert r.status_code == 422

    def test_chat_message_too_long(self):
        r = self.client.post("/chat/", json={"message": "x" * 2001})
        assert r.status_code == 422

    def test_root_endpoint(self):
        r = self.client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "running"

    def test_chat_response_shape(self):
        r = self.client.post("/chat/", json={"message": "I feel tired all day"})
        assert r.status_code == 200
        body = r.json()
        # Verify all required fields exist
        assert isinstance(body["reply"], str)
        assert isinstance(body["extracted"]["symptoms"], list)
        assert isinstance(body["safe"], bool)
