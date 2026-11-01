
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

    check_duplicate_registration([1, 2, 3], 4)

    check_duplicate_registration([1, 2, 3], 4)


import pytest


def make_participant(client, name="Amine", email="amine@example.com"):
    response = client.post("/participants/", json={"name": name, "email": email})
    assert response.status_code == 201, response.text
    return response.json()


# CREATE

def test_create_participant_returns_full_body(client):
    response = client.post(
        "/participants/", json={"name": "Amine", "email": "amine@example.com"}
    )
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body == {"id": body["id"], "name": "Amine", "email": "amine@example.com"}


def test_create_participant_is_persisted(client):
    created = make_participant(client)
    fetched = client.get(f"/participants/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_create_duplicate_email_conflict(client):
    make_participant(client, name="Amine", email="dup@example.com")
    response = client.post(
        "/participants/", json={"name": "Other Name", "email": "dup@example.com"}
    )
    assert response.status_code == 409
    assert response.json() == {"detail": "Email is already registered."}
    assert len(client.get("/participants/").json()) == 1


def test_create_different_emails_allowed(client):
    first = make_participant(client, name="Amine", email="a@example.com")
    second = make_participant(client, name="Amine", email="b@example.com")
    assert first["id"] != second["id"]
    assert len(client.get("/participants/").json()) == 2


@pytest.mark.parametrize("payload", [
    {"name": "A", "email": "a@example.com"},
    {"name": "N" * 101, "email": "a@example.com"},
    {"name": "Amine", "email": "not-an-email"},
    {"name": "Amine", "email": "a@b"},
    {"name": "Amine"},
    {"email": "a@example.com"},
])
def test_create_participant_invalid_payload(client, payload):
    assert client.post("/participants/", json=payload).status_code == 422
    assert client.get("/participants/").json() == []


def test_create_participant_boundary_names(client):
    assert client.post(
        "/participants/", json={"name": "Al", "email": "a@example.com"}
    ).status_code == 201
    assert client.post(
        "/participants/", json={"name": "N" * 100, "email": "b@example.com"}
    ).status_code == 201


# LIST

def test_list_participants_empty(client):
    response = client.get("/participants/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_participants_sorted_by_name(client):
    make_participant(client, name="Zed", email="z@example.com")
    make_participant(client, name="Amine", email="a@example.com")
    make_participant(client, name="Mina", email="m@example.com")
    names = [p["name"] for p in client.get("/participants/").json()]
    assert names == ["Amine", "Mina", "Zed"]


# GET ONE

def test_get_participant(client):
    created = make_participant(client)
    response = client.get(f"/participants/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_participant_picks_the_right_one(client):
    first = make_participant(client, name="First", email="f@example.com")
    second = make_participant(client, name="Second", email="s@example.com")
    assert client.get(f"/participants/{first['id']}").json()["name"] == "First"
    assert client.get(f"/participants/{second['id']}").json()["name"] == "Second"


def test_get_participant_not_found(client):
    response = client.get("/participants/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found."}


def test_get_participant_invalid_id(client):
    assert client.get("/participants/abc").status_code == 422


# DELETE

def test_delete_participant(client):
    created = make_participant(client)
    response = client.delete(f"/participants/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/participants/{created['id']}").status_code == 404
    assert client.get("/participants/").json() == []


def test_delete_participant_not_found(client):
    response = client.delete("/participants/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found."}


def test_delete_participant_keeps_others(client):
    first = make_participant(client, name="First", email="f@example.com")
    second = make_participant(client, name="Second", email="s@example.com")
    client.delete(f"/participants/{first['id']}")
    remaining = client.get("/participants/").json()
    assert [p["id"] for p in remaining] == [second["id"]]


def test_delete_participant_frees_the_email(client):
    created = make_participant(client, email="again@example.com")
    client.delete(f"/participants/{created['id']}")
    make_participant(client, email="again@example.com")


# ROUTER CONFIGURATION (through OpenAPI)

def test_participants_openapi_configuration(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert "/participants/" in paths
    assert "/participants/{participant_id}" in paths
    assert paths["/participants/"]["post"]["tags"] == ["Participants"]
    assert paths["/participants/"]["get"]["tags"] == ["Participants"]
    assert "201" in paths["/participants/"]["post"]["responses"]
    assert "204" in paths["/participants/{participant_id}"]["delete"]["responses"]


import importlib.util
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.database as database
import app.main as main
from app.database import get_db
from app.participant_utils import (
    check_duplicate_registration,
    has_available_capacity,
)


# PARTICIPANT UTILS

def test_duplicate_registration_message_contains_id():
    with pytest.raises(ValueError) as exc:
        check_duplicate_registration([1, 2, 3], 2)
    assert str(exc.value) == "Participant 2 is already registered"


def test_duplicate_registration_message_uses_new_id():
    with pytest.raises(ValueError) as exc:
        check_duplicate_registration(["a", "b"], "b")
    assert str(exc.value) == "Participant b is already registered"


def test_duplicate_check_empty_list_allowed():
    assert check_duplicate_registration([], 1) is None


def test_capacity_edge_cases():
    assert has_available_capacity(0, 1) is True
    assert has_available_capacity(0, 0) is False
    assert has_available_capacity(1, 1) is False


# DATABASE

def load_database_copy():
    """Execute database.py as a separate module with the factories patched."""
    spec = importlib.util.spec_from_file_location("database_probe", database.__file__)
    module = importlib.util.module_from_spec(spec)
    with patch("sqlalchemy.create_engine") as create_engine, \
         patch("sqlalchemy.orm.sessionmaker") as sessionmaker:
        spec.loader.exec_module(module)
    return module, create_engine, sessionmaker


def test_engine_configuration():
    module, create_engine, _ = load_database_copy()
    assert module.DATABASE_URL == "sqlite:///./events.db"
    create_engine.assert_called_once_with(
        "sqlite:///./events.db",
        connect_args={"check_same_thread": False},
    )
    assert module.engine is create_engine.return_value


def test_session_factory_configuration():
    module, create_engine, sessionmaker = load_database_copy()
    sessionmaker.assert_called_once_with(
        autocommit=False,
        autoflush=False,
        bind=create_engine.return_value,
    )
    assert module.SessionLocal is sessionmaker.return_value


def test_base_is_a_declarative_base():
    module, _, _ = load_database_copy()
    assert hasattr(module.Base, "metadata")
    assert hasattr(database.Base, "metadata")
    assert {"events", "participants", "registrations"} <= set(
        database.Base.metadata.tables
    )


def test_get_db_yields_session_and_closes_it():
    with patch("app.database.SessionLocal") as session_local:
        gen = get_db()
        db = next(gen)
        assert db is session_local.return_value
        db.close.assert_not_called()
        gen.close()
        db.close.assert_called_once()


def test_get_db_closes_session_on_error():
    with patch("app.database.SessionLocal") as session_local:
        gen = get_db()
        db = next(gen)
        with pytest.raises(RuntimeError):
            gen.throw(RuntimeError("boom"))
        db.close.assert_called_once()
        assert db is session_local.return_value


# MAIN

def load_main_copy():
    """Execute main.py as a separate module (sibling of app.main)."""
    spec = importlib.util.spec_from_file_location("app.main_probe", main.__file__)
    module = importlib.util.module_from_spec(spec)
    with patch("sqlalchemy.MetaData.create_all") as create_all:
        spec.loader.exec_module(module)
    return module, create_all


def test_main_creates_tables_with_engine():
    _, create_all = load_main_copy()
    create_all.assert_called_once_with(bind=database.engine)


def test_main_app_metadata():
    module, _ = load_main_copy()
    assert module.app.title == "Event Manager API"
    assert module.app.description == "A teaching project for Git, Docker and CI/CD"
    assert module.app.version == "1.0.0"


def test_main_includes_all_routers():
    module, _ = load_main_copy()
    paths = TestClient(module.app).get("/openapi.json").json()["paths"]
    assert "/events/" in paths
    assert "/events/{event_id}" in paths
    assert "/participants/" in paths
    assert "/participants/{participant_id}" in paths
    assert "/events/{event_id}/register/{participant_id}" in paths
    assert "/events/{event_id}/participants" in paths


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Event Manager API"}


def test_openapi_info(client):
    info = client.get("/openapi.json").json()["info"]
    assert info["title"] == "Event Manager API"
    assert info["version"] == "1.0.0"
    assert info["description"] == "A teaching project for Git, Docker and CI/CD"

