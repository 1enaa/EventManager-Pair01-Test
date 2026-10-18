import pytest
from pydantic import ValidationError

from app.schemas import ParticipantCreate
from app.participant_utils import (
    has_available_capacity,
    check_duplicate_registration,
)


# HAPPY PATH

def test_valid_participant_creation(sample_participant_dict):
    participant = ParticipantCreate(**sample_participant_dict)

    assert participant.name == "Amine"
    assert participant.email == "amine@example.com"


def test_capacity_available():
    assert has_available_capacity(5, 10) is True


# BOUNDARY TESTS

def test_capacity_one_below_max():
    assert has_available_capacity(9, 10) is True


def test_capacity_exactly_at_max():
    assert has_available_capacity(10, 10) is False


def test_capacity_above_max():
    assert has_available_capacity(11, 10) is False


def test_name_minimum_length(sample_participant_dict):
    data = {**sample_participant_dict, "name": "Al"}

    assert ParticipantCreate(**data).name == "Al"


# NEGATIVE TESTS

def test_name_too_short(sample_participant_dict):
    data = {**sample_participant_dict, "name": "A"}

    with pytest.raises(ValidationError):
        ParticipantCreate(**data)


@pytest.mark.parametrize(
    "bad_email", ["not-an-email", "missing@domain", "@example.com", ""]
)
def test_invalid_email(sample_participant_dict, bad_email):
    data = {**sample_participant_dict, "email": bad_email}

    with pytest.raises(ValidationError):
        ParticipantCreate(**data)


def test_duplicate_registration_raises():
    with pytest.raises(ValueError):
        check_duplicate_registration([1, 2, 3], 2)


def test_new_registration_is_allowed():
    # must not raise
    check_duplicate_registration([1, 2, 3], 4)
