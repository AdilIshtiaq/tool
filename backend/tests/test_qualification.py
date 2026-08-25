import pytest

from app.models import QualificationRule
from app.services.qualification import evaluate_rule, is_valid_field_operator, run_qualification


def _rule(field, operator, expected_value=None, **kwargs):
    kwargs.setdefault("enabled", True)
    kwargs.setdefault("priority", 0)
    return QualificationRule(
        name="test rule",
        field=field,
        operator=operator,
        expected_value=expected_value,
        **kwargs,
    )


class TestEvaluateRule:
    def test_exists_true_when_present(self, make_lead):
        lead = make_lead(website="https://example.com")
        assert evaluate_rule(lead, _rule("website", "exists")) is True

    def test_exists_false_when_missing(self, make_lead):
        lead = make_lead(website=None)
        assert evaluate_rule(lead, _rule("website", "exists")) is False

    def test_not_exists_true_when_missing(self, make_lead):
        lead = make_lead(website=None)
        assert evaluate_rule(lead, _rule("website", "not_exists")) is True

    def test_equals_case_insensitive(self, make_lead):
        lead = make_lead(category="Restaurant")
        assert evaluate_rule(lead, _rule("category", "equals", "restaurant")) is True

    def test_not_equals(self, make_lead):
        lead = make_lead(category="Hotel")
        assert evaluate_rule(lead, _rule("category", "not_equals", "restaurant")) is True

    def test_contains(self, make_lead):
        lead = make_lead(city="New Lahore City")
        assert evaluate_rule(lead, _rule("city", "contains", "lahore")) is True

    def test_in_list(self, make_lead):
        lead = make_lead(category="Hotel")
        assert evaluate_rule(lead, _rule("category", "in", "Hotel, Restaurant, Cafe")) is True

    def test_not_in_list(self, make_lead):
        lead = make_lead(category="Government")
        assert evaluate_rule(lead, _rule("category", "not_in", "Hotel, Restaurant, Cafe")) is True

    def test_greater_than(self, make_lead):
        lead = make_lead(rating=4.5)
        assert evaluate_rule(lead, _rule("rating", "greater_than", "4.0")) is True

    def test_greater_than_false_when_below(self, make_lead):
        lead = make_lead(rating=3.0)
        assert evaluate_rule(lead, _rule("rating", "greater_than", "4.0")) is False

    def test_less_than(self, make_lead):
        lead = make_lead(review_count=10)
        assert evaluate_rule(lead, _rule("review_count", "less_than", "100")) is True

    def test_numeric_operator_false_on_missing_value(self, make_lead):
        lead = make_lead(rating=None)
        assert evaluate_rule(lead, _rule("rating", "greater_than", "4.0")) is False


class TestFieldOperatorValidation:
    def test_valid_combination(self):
        assert is_valid_field_operator("website", "exists") is True

    def test_invalid_operator_for_field(self):
        assert is_valid_field_operator("website", "contains") is False

    def test_unknown_field(self):
        assert is_valid_field_operator("not_a_real_field", "exists") is False


class TestRunQualification:
    def test_all_rules_pass_yields_qualified(self, db_session, make_lead):
        lead = make_lead(website="https://example.com", phone="0300", rating=4.8)
        db_session.add(_rule("website", "exists", priority=1))
        db_session.add(_rule("phone", "exists", priority=2))
        db_session.commit()

        result = run_qualification(db_session, lead)
        assert result.result == "qualified"
        assert result.score == 100.0
        assert lead.status == "qualified"

    def test_all_rules_fail_yields_not_qualified(self, db_session, make_lead):
        lead = make_lead(website=None, phone=None)
        db_session.add(_rule("website", "exists", priority=1))
        db_session.add(_rule("phone", "exists", priority=2))
        db_session.commit()

        result = run_qualification(db_session, lead)
        assert result.result == "not_qualified"
        assert result.score == 0.0

    def test_mixed_results_yield_needs_review(self, db_session, make_lead):
        lead = make_lead(website="https://example.com", phone=None)
        db_session.add(_rule("website", "exists", priority=1))
        db_session.add(_rule("phone", "exists", priority=2))
        db_session.commit()

        result = run_qualification(db_session, lead)
        assert result.result == "needs_review"
        assert result.score == 50.0

    def test_no_enabled_rules_yields_needs_review(self, db_session, make_lead):
        lead = make_lead()
        result = run_qualification(db_session, lead)
        assert result.result == "needs_review"
        assert result.score == 0.0

    def test_disabled_rules_are_ignored(self, db_session, make_lead):
        lead = make_lead(website=None)
        db_session.add(_rule("website", "exists", priority=1, enabled=False))
        db_session.commit()

        result = run_qualification(db_session, lead)
        assert result.result == "needs_review"  # zero enabled rules
