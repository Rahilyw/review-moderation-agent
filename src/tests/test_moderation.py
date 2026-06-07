# src/tests/test_moderation.py — run with: pytest src/tests/test_moderation.py -v
import sys
sys.path.insert(0, "src")
from importlib import import_module

mod = import_module("02_comment_moderation")
apply_moderation = mod.apply_moderation
classify_comment = mod.classify_comment


class TestApplyModeration:
    """Unit tests for the business-logic layer (no model calls)."""

    def test_safe_high_confidence_approved(self):
        assert apply_moderation({"classification": "SAFE", "confidence": 0.95}) == "APPROVED"

    def test_safe_low_confidence_flagged(self):
        assert apply_moderation({"classification": "SAFE", "confidence": 0.5}) == "FLAGGED_FOR_REVIEW"

    def test_safe_at_threshold_approved(self):
        assert apply_moderation({"classification": "SAFE", "confidence": 0.8}) == "APPROVED"

    def test_unsafe_high_confidence_blocked(self):
        assert apply_moderation({"classification": "UNSAFE", "confidence": 0.9}) == "BLOCKED"

    def test_unsafe_low_confidence_flagged(self):
        assert apply_moderation({"classification": "UNSAFE", "confidence": 0.3}) == "FLAGGED_FOR_REVIEW"

    def test_unsafe_at_threshold_blocked(self):
        assert apply_moderation({"classification": "UNSAFE", "confidence": 0.7}) == "BLOCKED"

    def test_needs_review_always_flagged(self):
        assert apply_moderation({"classification": "NEEDS_REVIEW", "confidence": 0.99}) == "FLAGGED_FOR_REVIEW"

    def test_missing_classification_flagged(self):
        assert apply_moderation({"confidence": 0.9}) == "FLAGGED_FOR_REVIEW"

    def test_missing_confidence_flagged(self):
        assert apply_moderation({"classification": "SAFE"}) == "FLAGGED_FOR_REVIEW"
