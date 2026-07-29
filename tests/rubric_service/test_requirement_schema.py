import pytest
from pydantic import ValidationError

from services.rubric_service.requirement import ObjectiveCriterion, Requirement, SubjectiveCriterion


def test_requires_at_least_one_criterion():
    with pytest.raises(ValidationError):
        Requirement()


def test_accepts_objective_only():
    req = Requirement(objective_criteria=[ObjectiveCriterion(field="lead_count", comparator=">=", value=100)])
    assert req.subjective_criteria == []


def test_accepts_subjective_only_when_weights_sum_to_one():
    req = Requirement(subjective_criteria=[SubjectiveCriterion(description="a", weight=1.0)])
    assert req.objective_criteria == []


def test_subjective_weights_must_sum_to_one():
    with pytest.raises(ValidationError):
        Requirement(
            subjective_criteria=[
                SubjectiveCriterion(description="a", weight=0.3),
                SubjectiveCriterion(description="b", weight=0.3),
            ]
        )


def test_subjective_weights_summing_to_one_is_accepted():
    req = Requirement(
        subjective_criteria=[
            SubjectiveCriterion(description="a", weight=0.6),
            SubjectiveCriterion(description="b", weight=0.4),
        ]
    )
    assert len(req.subjective_criteria) == 2


def test_subjective_criterion_weight_must_be_in_0_1_range():
    with pytest.raises(ValidationError):
        SubjectiveCriterion(description="a", weight=1.5)
    with pytest.raises(ValidationError):
        SubjectiveCriterion(description="a", weight=0)


def test_objective_schema_maps_field_to_inferred_type():
    req = Requirement(
        objective_criteria=[
            ObjectiveCriterion(field="lead_count", comparator=">=", value=100),
            ObjectiveCriterion(field="company_name", comparator="==", value="Acme"),
        ]
    )
    assert req.objective_schema() == {"lead_count": "integer", "company_name": "string"}


def test_objective_schema_is_empty_when_there_are_no_objective_criteria():
    req = Requirement(subjective_criteria=[SubjectiveCriterion(description="a", weight=1.0)])
    assert req.objective_schema() == {}
