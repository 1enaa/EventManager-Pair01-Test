
import pytest
from pydantic import ValidationError

from app.schemas import EventCreate
from app.event_utils import (
    filter_events_by_location,
    filter_events_by_title,
)




def test_valid_event_creation(sample_event_dict):
    event = EventCreate(**sample_event_dict)

    assert event.title == "Cybersecurity Workshop"
    assert event.location == "Constantine"
    assert event.capacity == 100


def test_filter_events_by_location(prepopulated_event_store):
    results = filter_events_by_location(
        prepopulated_event_store, "constantine"
    )

    assert len(results) == 2
    assert all(
        "constantine" in event["location"].casefold()
        for event in results
    )


def test_filter_events_by_title(prepopulated_event_store):
    results = filter_events_by_title(
        prepopulated_event_store, "CYBERSECURITY"
    )

    assert len(results) == 2


# BOUNDARY TESTS

def test_title_minimum_length(sample_event_dict):
    data = {**sample_event_dict, "title": "ABC"}

    event = EventCreate(**data)

    assert event.title == "ABC"


def test_capacity_minimum(sample_event_dict):
    data = {**sample_event_dict, "capacity": 1}

    event = EventCreate(**data)

    assert event.capacity == 1


def test_capacity_maximum(sample_event_dict):
    data = {**sample_event_dict, "capacity": 10000}

    event = EventCreate(**data)

    assert event.capacity == 10000


# NEGATIVE TESTS

def test_title_too_short(sample_event_dict):
    data = {**sample_event_dict, "title": "AB"}

    with pytest.raises(ValidationError):
        EventCreate(**data)


@pytest.mark.parametrize("capacity", [0, -1, 10001])
def test_invalid_capacity(sample_event_dict, capacity):
    data = {**sample_event_dict, "capacity": capacity}

    with pytest.raises(ValidationError):
        EventCreate(**data)

