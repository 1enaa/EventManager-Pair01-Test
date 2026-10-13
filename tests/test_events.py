
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

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.models import Event
from app.routers import events as event_routes
from app.schemas import EventCreate, EventUpdate


def make_event(**overrides):
    data = {
        "id": 1,
        "title": "Cybersecurity Workshop",
        "description": "A cybersecurity workshop.",
        "date": date(2099, 11, 15),
        "location": "Constantine",
        "capacity": 100,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_db():
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    return db, query


# CREATE EVENT

def test_create_event_with_mocked_db():
    db, _ = make_db()
    payload = EventCreate(
        title="Cybersecurity Workshop",
        description="A cybersecurity workshop.",
        date="2099-11-15",
        location="Constantine",
        capacity=100,
    )

    result = event_routes.create_event(payload, db)

    assert result.title == payload.title
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_event_rejects_past_date():
    db, _ = make_db()
    payload = EventCreate(
        title="Cybersecurity Workshop",
        description="A workshop.",
        date="2000-01-01",
        location="Constantine",
        capacity=100,
    )

    with pytest.raises(HTTPException) as exc:
        event_routes.create_event(payload, db)

    assert exc.value.status_code == 400
    db.add.assert_not_called()


# LIST AND FILTER EVENTS

def test_list_events_without_filters():
    db, query = make_db()
    expected = [make_event(), make_event(id=2)]
    query.order_by.return_value.all.return_value = expected

    result = event_routes.list_events(
        search=None, location=None, db=db
    )

    assert result == expected
    query.filter.assert_not_called()
    query.order_by.assert_called_once()


def test_list_events_with_search_and_location():
    db, query = make_db()
    expected = [make_event()]
    query.order_by.return_value.all.return_value = expected

    result = event_routes.list_events(
        search="Cyber",
        location="Constantine",
        db=db,
    )

    assert result == expected
    assert query.filter.call_count == 2


# GET EVENT

def test_get_existing_event():
    db, query = make_db()
    expected = make_event()
    query.first.return_value = expected

    result = event_routes.get_event(1, db)

    assert result is expected


def test_get_missing_event():
    db, query = make_db()
    query.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        event_routes.get_event(999, db)

    assert exc.value.status_code == 404


# UPDATE EVENT

def test_update_existing_event():
    db, query = make_db()
    existing = make_event()
    query.first.return_value = existing

    payload = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date="2099-12-01",
        location="Algiers",
        capacity=200,
    )

    result = event_routes.update_event(1, payload, db)

    assert result.title == "Updated Workshop"
    assert result.location == "Algiers"
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_update_missing_event():
    db, query = make_db()
    query.first.return_value = None

    payload = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date="2099-12-01",
        location="Algiers",
        capacity=200,
    )

    with pytest.raises(HTTPException) as exc:
        event_routes.update_event(999, payload, db)

    assert exc.value.status_code == 404
    db.commit.assert_not_called()


def test_update_event_rejects_past_date():
    db, query = make_db()
    query.first.return_value = make_event()

    payload = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date="2000-01-01",
        location="Algiers",
        capacity=200,
    )

    with pytest.raises(HTTPException) as exc:
        event_routes.update_event(1, payload, db)

    assert exc.value.status_code == 400
    db.commit.assert_not_called()


# DELETE EVENT

def test_delete_existing_event():
    db, query = make_db()
    query.first.return_value = make_event()

    result = event_routes.delete_event(1, db)

    assert result is None
    db.delete.assert_called_once()
    db.commit.assert_called_once()


def test_delete_missing_event():
    db, query = make_db()
    query.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        event_routes.delete_event(999, db)

    assert exc.value.status_code == 404
    db.delete.assert_not_called()
