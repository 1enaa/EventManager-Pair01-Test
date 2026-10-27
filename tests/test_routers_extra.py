
"""Extra tests covering participants and registrations routers,
database.get_db and main.py, using mocks only:
no live database and no HTTP calls."""

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.sql import operators

from app.database import get_db
from app.models import Event, Participant, Registration
from app.routers import participants as participant_routes
from app.routers import registrations as registration_routes
from app.schemas import ParticipantCreate


# ======================================================================
# PARTICIPANTS ROUTER
# ======================================================================

def make_participant_db():
    db = MagicMock()
    query = MagicMock()
    db.query.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    return db, query


def make_participant_model(**overrides):
    data = {
        "id": 1,
        "name": "Amine",
        "email": "amine@example.com",
    }
    data.update(overrides)
    return Participant(**data)


def test_create_participant_success(sample_participant_dict):
    db, query = make_participant_db()
    query.first.return_value = None
    payload = ParticipantCreate(**sample_participant_dict)

    result = participant_routes.create_participant(payload, db)

    assert result.name == payload.name
    assert result.email == payload.email
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_participant_duplicate_email(sample_participant_dict):
    db, query = make_participant_db()
    query.first.return_value = make_participant_model()
    payload = ParticipantCreate(**sample_participant_dict)

    with pytest.raises(HTTPException) as exc:
        participant_routes.create_participant(payload, db)

    assert exc.value.status_code == 409
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_list_participants():
    db, query = make_participant_db()
    expected = [
        make_participant_model(),
        make_participant_model(id=2, name="Sara"),
    ]
    query.all.return_value = expected

    result = participant_routes.list_participants(db)

    assert result == expected
    query.order_by.assert_called_once()


def test_get_existing_participant():
    db, query = make_participant_db()
    expected = make_participant_model()
    query.first.return_value = expected

    assert participant_routes.get_participant(1, db) is expected


def test_get_missing_participant():
    db, query = make_participant_db()
    query.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        participant_routes.get_participant(999, db)

    assert exc.value.status_code == 404


def test_delete_existing_participant():
    db, query = make_participant_db()
    query.first.return_value = make_participant_model()

    result = participant_routes.delete_participant(1, db)

    assert result is None
    db.delete.assert_called_once()
    db.commit.assert_called_once()


def test_delete_missing_participant():
    db, query = make_participant_db()
    query.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        participant_routes.delete_participant(999, db)

    assert exc.value.status_code == 404
    db.delete.assert_not_called()


# ======================================================================
# REGISTRATIONS ROUTER: HELPERS
# ======================================================================

def make_registration_db(event=None, participant=None, existing=None):
    """Return a mocked session with results selected by model."""
    results = {
        Event: event,
        Participant: participant,
        Registration: existing,
    }
    db = MagicMock()

    def query(model):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = results[model]
        return q

    db.query.side_effect = query
    return db


def make_tracking_registration_db(event=None, participant=None, existing=None):
    """Return a mocked session and retain query objects for assertions."""
    results = {
        Event: event,
        Participant: participant,
        Registration: existing,
    }
    queries = {}
    db = MagicMock()

    def query(model):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = results[model]
        queries[model] = q
        return q

    db.query.side_effect = query
    return db, queries


def make_event(registrations=None, capacity=10):
    return SimpleNamespace(
        id=1,
        capacity=capacity,
        registrations=registrations or [],
    )


def make_simple_participant():
    return SimpleNamespace(
        id=5,
        name="Amine",
        email="amine@example.com",
    )


# ======================================================================
# REGISTRATIONS ROUTER: CONFIGURATION
# ======================================================================

def test_registration_router_configuration_and_routes():
    assert registration_routes.router is not None
    assert registration_routes.router.prefix == "/events"
    assert registration_routes.router.tags == ["Registrations"]

    registered_routes = {
        (route.path, method)
        for route in registration_routes.router.routes
        for method in getattr(route, "methods", set())
    }

    # FastAPI stores the full paths, including the router prefix.
    assert (
        "/events/{event_id}/register/{participant_id}",
        "POST",
    ) in registered_routes

    assert (
        "/events/{event_id}/participants",
        "GET",
    ) in registered_routes


# ======================================================================
# REGISTRATIONS ROUTER: REGISTER PARTICIPANT
# ======================================================================

def test_register_participant_success():
    db = make_registration_db(
        event=make_event(),
        participant=make_simple_participant(),
    )

    result = registration_routes.register_participant(1, 5, db)

    assert result.event_id == 1
    assert result.participant_id == 5
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_register_event_not_found():
    db = make_registration_db(event=None)

    with pytest.raises(HTTPException) as exc:
        registration_routes.register_participant(999, 5, db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Event not found."
    db.add.assert_not_called()


def test_register_participant_not_found():
    db = make_registration_db(
        event=make_event(),
        participant=None,
    )

    with pytest.raises(HTTPException) as exc:
        registration_routes.register_participant(1, 999, db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Participant not found."
    db.add.assert_not_called()


def test_register_duplicate_registration():
    db = make_registration_db(
        event=make_event(),
        participant=make_simple_participant(),
        existing=SimpleNamespace(id=1),
    )

    with pytest.raises(HTTPException) as exc:
        registration_routes.register_participant(1, 5, db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Participant is already registered."
    db.commit.assert_not_called()


def test_register_event_full():
    event = make_event(
        registrations=[object(), object()],
        capacity=2,
    )
    db = make_registration_db(
        event=event,
        participant=make_simple_participant(),
    )

    with pytest.raises(HTTPException) as exc:
        registration_routes.register_participant(1, 5, db)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Event capacity has been reached."
    db.add.assert_not_called()


def test_register_last_free_seat():
    event = make_event(registrations=[object()], capacity=2)
    db = make_registration_db(
        event=event,
        participant=make_simple_participant(),
    )

    result = registration_routes.register_participant(1, 5, db)

    assert result.participant_id == 5
    db.add.assert_called_once()
    db.commit.assert_called_once()


# ======================================================================
# REGISTRATIONS ROUTER: FILTER OPERATOR MUTANTS
# ======================================================================

def test_register_event_filter_uses_equality():
    db, queries = make_tracking_registration_db(
        event=make_event(),
        participant=make_simple_participant(),
    )

    registration_routes.register_participant(1, 5, db)

    expression = queries[Event].filter.call_args.args[0]
    assert expression.operator is operators.eq


def test_register_participant_filter_uses_equality():
    db, queries = make_tracking_registration_db(
        event=make_event(),
        participant=make_simple_participant(),
    )

    registration_routes.register_participant(1, 5, db)

    expression = queries[Participant].filter.call_args.args[0]
    assert expression.operator is operators.eq


def test_duplicate_registration_filters_use_equality():
    db, queries = make_tracking_registration_db(
        event=make_event(),
        participant=make_simple_participant(),
    )

    registration_routes.register_participant(1, 5, db)

    expressions = queries[Registration].filter.call_args.args

    assert len(expressions) == 2
    assert all(
        expression.operator is operators.eq
        for expression in expressions
    )


# ======================================================================
# REGISTRATIONS ROUTER: LIST EVENT PARTICIPANTS
# ======================================================================

def test_list_event_participants_success():
    registrations = [
        SimpleNamespace(participant=make_simple_participant())
    ]
    db = make_registration_db(
        event=make_event(registrations=registrations),
    )

    result = registration_routes.list_event_participants(1, db)

    assert result == [
        {"id": 5, "name": "Amine", "email": "amine@example.com"}
    ]


def test_list_event_participants_multiple():
    participant_one = make_simple_participant()
    participant_two = SimpleNamespace(
        id=6,
        name="Sara",
        email="sara@example.com",
    )
    registrations = [
        SimpleNamespace(participant=participant_one),
        SimpleNamespace(participant=participant_two),
    ]
    db = make_registration_db(
        event=make_event(registrations=registrations),
    )

    result = registration_routes.list_event_participants(1, db)

    assert result == [
        {"id": 5, "name": "Amine", "email": "amine@example.com"},
        {"id": 6, "name": "Sara", "email": "sara@example.com"},
    ]


def test_list_event_participants_empty():
    db = make_registration_db(event=make_event())

    assert registration_routes.list_event_participants(1, db) == []


def test_list_event_participants_event_not_found():
    db = make_registration_db(event=None)

    with pytest.raises(HTTPException) as exc:
        registration_routes.list_event_participants(999, db)

    assert exc.value.status_code == 404
    assert exc.value.detail == "Event not found."


def test_list_event_participants_filter_uses_equality():
    db, queries = make_tracking_registration_db(
        event=make_event(),
    )

    registration_routes.list_event_participants(1, db)

    expression = queries[Event].filter.call_args.args[0]
    assert expression.operator is operators.eq


# ======================================================================
# DATABASE
# ======================================================================

def test_get_db_yields_session_and_closes_it():
    with patch("app.database.SessionLocal") as session_local:
        gen = get_db()
        db = next(gen)

        assert db is session_local.return_value
        db.close.assert_not_called()

        gen.close()

        db.close.assert_called_once()


# ======================================================================
# MAIN APPLICATION
# ======================================================================

def test_main_app_setup_and_root_endpoint():
    with patch("sqlalchemy.MetaData.create_all") as create_all:
        import app.main as main
        importlib.reload(main)

    create_all.assert_called()
    assert main.app.title == "Event Manager API"
    assert main.root() == {
        "message": "Welcome to Event Manager API"
    }
