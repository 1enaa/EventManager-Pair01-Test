
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.sql import operators

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


def assert_event_id_filter(query, expected_id):
    expression = query.filter.call_args.args[0]

    assert expression.left == Event.id
    assert expression.operator == operators.eq
    assert expression.right.value == expected_id


# --------------------------------------------------
# Route registration
# --------------------------------------------------

def test_all_event_routes_are_registered():
    registered = {
        (method, route.path)
        for route in event_routes.router.routes
        for method in route.methods
    }

    assert ("POST", "/events/") in registered
    assert ("GET", "/events/") in registered
    assert ("GET", "/events/{event_id}") in registered
    assert ("PUT", "/events/{event_id}") in registered
    assert ("DELETE", "/events/{event_id}") in registered


# --------------------------------------------------
# Create event
# --------------------------------------------------

def test_create_event_success():
    db, _ = make_db()

    event_data = EventCreate(
        title="Cybersecurity Workshop",
        description="A cybersecurity workshop.",
        date=date(2099, 11, 15),
        location="Constantine",
        capacity=100,
    )

    result = event_routes.create_event(event_data, db)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()

    assert result.title == event_data.title
    assert result.location == event_data.location
    assert result.capacity == event_data.capacity


def test_create_event_allows_today(monkeypatch):
    today = date(2026, 10, 20)
    monkeypatch.setattr(event_routes, "date", SimpleNamespace(today=lambda: today))

    db, _ = make_db()

    event_data = EventCreate(
        title="Today's Workshop",
        description="A workshop happening today.",
        date=today,
        location="Constantine",
        capacity=100,
    )

    result = event_routes.create_event(event_data, db)

    assert result.title == event_data.title
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_create_event_rejects_past_date(monkeypatch):
    today = date(2026, 10, 20)
    monkeypatch.setattr(event_routes, "date", SimpleNamespace(today=lambda: today))

    db, _ = make_db()

    event_data = EventCreate(
        title="Past Workshop",
        description="A workshop in the past.",
        date=date(2026, 10, 19),
        location="Constantine",
        capacity=100,
    )

    with pytest.raises(HTTPException) as exc_info:
        event_routes.create_event(event_data, db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Event date cannot be in the past."

    db.add.assert_not_called()
    db.commit.assert_not_called()


# --------------------------------------------------
# List events
# --------------------------------------------------

def test_list_events_without_filters():
    db, query = make_db()
    expected_events = [
        make_event(id=1),
        make_event(id=2, title="Networking Workshop"),
    ]
    query.order_by.return_value.all.return_value = expected_events

    result = event_routes.list_events(
        search=None,
        location=None,
        db=db,
    )

    assert result == expected_events
    db.query.assert_called_once_with(Event)
    query.order_by.assert_called_once_with(Event.date)
    query.order_by.return_value.all.assert_called_once()


def test_list_events_with_search_and_location():
    db, query = make_db()
    query.order_by.return_value.all.return_value = [make_event()]

    result = event_routes.list_events(
        search="Cyber",
        location="Constantine",
        db=db,
    )

    assert len(result) == 1
    assert query.filter.call_count == 2

    first_filter = query.filter.call_args_list[0].args[0]
    second_filter = query.filter.call_args_list[1].args[0]

    assert first_filter.right.value == "%Cyber%"
    assert second_filter.right.value == "%Constantine%"


def test_list_events_search_is_case_insensitive():
    db, query = make_db()
    query.order_by.return_value.all.return_value = []

    event_routes.list_events(
        search="cYbEr",
        location=None,
        db=db,
    )

    search_filter = query.filter.call_args.args[0]

    # SQLAlchemy's ilike operator should be used for case-insensitive search.
    assert search_filter.operator.__name__ == "ilike_op"
    assert search_filter.right.value == "%cYbEr%"


def test_list_events_location_is_case_insensitive():
    db, query = make_db()
    query.order_by.return_value.all.return_value = []

    event_routes.list_events(
        search=None,
        location="cOnStAnTiNe",
        db=db,
    )

    location_filter = query.filter.call_args.args[0]

    assert location_filter.operator.__name__ == "ilike_op"
    assert location_filter.right.value == "%cOnStAnTiNe%"


# --------------------------------------------------
# Get event
# --------------------------------------------------

def test_get_event_success():
    db, query = make_db()
    expected_event = make_event(id=7)
    query.filter.return_value.first.return_value = expected_event

    result = event_routes.get_event(7, db)

    assert result == expected_event
    assert_event_id_filter(query, 7)


def test_get_event_not_found():
    db, query = make_db()
    query.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        event_routes.get_event(99, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."
    assert_event_id_filter(query, 99)


# --------------------------------------------------
# Update event
# --------------------------------------------------

def test_update_event_success():
    db, query = make_db()
    existing_event = make_event(id=5)
    query.filter.return_value.first.return_value = existing_event

    update_data = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date=date(2099, 12, 1),
        location="Algiers",
        capacity=200,
    )

    result = event_routes.update_event(5, update_data, db)

    assert result == existing_event
    assert existing_event.title == "Updated Workshop"
    assert existing_event.description == "Updated description."
    assert existing_event.location == "Algiers"
    assert existing_event.capacity == 200

    assert_event_id_filter(query, 5)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_event)


def test_update_event_allows_today(monkeypatch):
    today = date(2026, 10, 20)
    monkeypatch.setattr(event_routes, "date", SimpleNamespace(today=lambda: today))

    db, query = make_db()
    existing_event = make_event(id=5)
    query.filter.return_value.first.return_value = existing_event

    update_data = EventUpdate(
        title="Today's Workshop",
        description="Updated description.",
        date=today,
        location="Constantine",
        capacity=100,
    )

    event_routes.update_event(5, update_data, db)

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(existing_event)


def test_update_event_not_found():
    db, query = make_db()
    query.filter.return_value.first.return_value = None

    update_data = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date=date(2099, 12, 1),
        location="Algiers",
        capacity=200,
    )

    with pytest.raises(HTTPException) as exc_info:
        event_routes.update_event(99, update_data, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."
    assert_event_id_filter(query, 99)

    db.commit.assert_not_called()
    db.refresh.assert_not_called()


def test_update_event_rejects_past_date(monkeypatch):
    today = date(2026, 10, 20)
    monkeypatch.setattr(event_routes, "date", SimpleNamespace(today=lambda: today))

    db, query = make_db()
    existing_event = make_event(id=5)
    query.filter.return_value.first.return_value = existing_event

    update_data = EventUpdate(
        title="Updated Workshop",
        description="Updated description.",
        date=date(2026, 10, 19),
        location="Algiers",
        capacity=200,
    )

    with pytest.raises(HTTPException) as exc_info:
        event_routes.update_event(5, update_data, db)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Event date cannot be in the past."

    db.commit.assert_not_called()
    db.refresh.assert_not_called()


# --------------------------------------------------
# Delete event
# --------------------------------------------------

def test_delete_event_success():
    db, query = make_db()
    existing_event = make_event(id=8)
    query.filter.return_value.first.return_value = existing_event

    result = event_routes.delete_event(8, db)

    assert result is None
    assert_event_id_filter(query, 8)

    db.delete.assert_called_once_with(existing_event)
    db.commit.assert_called_once()


def test_delete_event_not_found():
    db, query = make_db()
    query.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        event_routes.delete_event(99, db)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found."
    assert_event_id_filter(query, 99)

    db.delete.assert_not_called()
    db.commit.assert_not_called()
