from datetime import date, timedelta

import pytest
from fastapi import APIRouter
from pydantic import ValidationError

from app.event_utils import (
    filter_events_by_location,
    filter_events_by_title,
)
from app.models import Event, Participant, Registration
from app.routers.events import router
from app.schemas import (
    Event as EventSchema,
    EventCreate,
    Participant as ParticipantSchema,
    ParticipantCreate,
    Registration as RegistrationSchema,
)


# EVENT CREATION TESTS

def test_valid_event_creation(sample_event_dict):
    event = EventCreate(**sample_event_dict)

    assert event.title == "Cybersecurity Workshop"
    assert event.location == "Constantine"
    assert event.capacity == 100


# EVENT FILTER TESTS

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
    assert all(
        "cybersecurity" in event["title"].casefold()
        for event in results
    )


def test_filter_events_by_title_mixed_case(prepopulated_event_store):
    results = filter_events_by_title(
        prepopulated_event_store, "cYbErSeCuRiTy"
    )

    assert len(results) == 2
    assert all(
        "cybersecurity" in event["title"].casefold()
        for event in results
    )


# TITLE VALIDATION TESTS

def test_title_minimum_length(sample_event_dict):
    data = {**sample_event_dict, "title": "ABC"}

    event = EventCreate(**data)

    assert event.title == "ABC"


def test_title_too_short(sample_event_dict):
    data = {**sample_event_dict, "title": "AB"}

    with pytest.raises(ValidationError):
        EventCreate(**data)


# CAPACITY VALIDATION TESTS

def test_capacity_minimum(sample_event_dict):
    data = {**sample_event_dict, "capacity": 1}

    event = EventCreate(**data)

    assert event.capacity == 1


def test_capacity_maximum(sample_event_dict):
    data = {**sample_event_dict, "capacity": 10000}

    event = EventCreate(**data)

    assert event.capacity == 10000


@pytest.mark.parametrize("capacity", [0, -1, 10001])
def test_invalid_capacity(sample_event_dict, capacity):
    data = {**sample_event_dict, "capacity": capacity}

    with pytest.raises(ValidationError):
        EventCreate(**data)


# ROUTER CONFIGURATION TESTS

def test_events_router_prefix():
    assert router.prefix == "/events"


def test_events_router_tags():
    assert router.tags == ["Events"]


def test_events_router_is_defined():
    assert isinstance(router, APIRouter)


def test_create_event_route_path():
    routes = [
        route
        for route in router.routes
        if "POST" in getattr(route, "methods", set())
    ]

    assert any(route.path == "/events/" for route in routes)


# ROUTER TESTS THROUGH THE HTTP LAYER
# (these exercise the endpoint functions, so mutmut maps them to the
# module-level router mutants)

def test_events_prefix_is_mounted(client):
    # kills prefix="XX/eventsXX"
    assert client.get("/events/").status_code == 200
    assert client.get("/XX/eventsXX/").status_code == 404


def test_events_router_registered_in_openapi(client):
    # kills router = None
    paths = client.get("/openapi.json").json()["paths"]
    assert "/events/" in paths
    assert "/events/{event_id}" in paths


def test_events_tag_in_openapi(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/events/"]["get"]["tags"] == ["Events"]


def test_create_and_get_event_via_api(client, sample_event_dict):
    created = client.post("/events/", json=sample_event_dict)
    assert created.status_code == 201

    fetched = client.get(f"/events/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Cybersecurity Workshop"



@pytest.fixture
def create_event(client, sample_event_dict):
    def _create(**overrides):
        response = client.post("/events/", json={**sample_event_dict, **overrides})
        assert response.status_code == 201, response.text
        return response.json()
    return _create


# CREATE

def test_create_event_returns_full_body(client, sample_event_dict):
    response = client.post("/events/", json=sample_event_dict)
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["title"] == sample_event_dict["title"]
    assert body["description"] == sample_event_dict["description"]
    assert body["date"] == sample_event_dict["date"]
    assert body["location"] == sample_event_dict["location"]
    assert body["capacity"] == sample_event_dict["capacity"]


def test_create_event_without_description(client, sample_event_dict):
    payload = {k: v for k, v in sample_event_dict.items() if k != "description"}
    response = client.post("/events/", json=payload)
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_event_today_is_allowed(client, sample_event_dict):
    today = date.today().isoformat()
    response = client.post("/events/", json={**sample_event_dict, "date": today})
    assert response.status_code == 201
    assert response.json()["date"] == today


def test_create_event_yesterday_rejected(client, sample_event_dict):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = client.post("/events/", json={**sample_event_dict, "date": yesterday})
    assert response.status_code == 400
    assert response.json() == {"detail": "Event date cannot be in the past."}


def test_create_event_rejected_is_not_saved(client, sample_event_dict):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post("/events/", json={**sample_event_dict, "date": yesterday})
    assert client.get("/events/").json() == []


@pytest.mark.parametrize("overrides", [
    {"title": "AB"},
    {"title": "A" * 101},
    {"location": "X"},
    {"location": "L" * 101},
    {"capacity": 0},
    {"capacity": 10001},
    {"date": "not-a-date"},
])
def test_create_event_invalid_payload(client, sample_event_dict, overrides):
    response = client.post("/events/", json={**sample_event_dict, **overrides})
    assert response.status_code == 422


def test_create_event_missing_title(client, sample_event_dict):
    payload = {k: v for k, v in sample_event_dict.items() if k != "title"}
    assert client.post("/events/", json=payload).status_code == 422


# LIST / FILTERS

def test_list_events_empty(client):
    response = client.get("/events/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_events_ordered_by_date(client, create_event):
    late = create_event(title="Late Event", date="2099-12-01")
    early = create_event(title="Early Event", date="2099-01-01")
    middle = create_event(title="Middle Event", date="2099-06-01")
    ids = [e["id"] for e in client.get("/events/").json()]
    assert ids == [early["id"], middle["id"], late["id"]]


def test_list_events_search_is_case_insensitive_and_partial(client, create_event):
    match = create_event(title="Cybersecurity Workshop")
    create_event(title="Python Training")
    for term in ["cyber", "CYBER", "cYbEr", "Workshop"]:
        results = client.get("/events/", params={"search": term}).json()
        assert [e["id"] for e in results] == [match["id"]]


def test_list_events_search_no_match(client, create_event):
    create_event(title="Cybersecurity Workshop")
    assert client.get("/events/", params={"search": "zzz"}).json() == []


def test_list_events_filter_by_location(client, create_event):
    a = create_event(title="Event A", location="Constantine")
    create_event(title="Event B", location="Algiers")
    for term in ["constantine", "CONST", "tine"]:
        results = client.get("/events/", params={"location": term}).json()
        assert [e["id"] for e in results] == [a["id"]]


def test_list_events_location_no_match(client, create_event):
    create_event(location="Constantine")
    assert client.get("/events/", params={"location": "Oran"}).json() == []


def test_list_events_search_and_location_combined(client, create_event):
    target = create_event(title="Cyber Day", location="Constantine")
    create_event(title="Cyber Night", location="Algiers")
    create_event(title="Python Day", location="Constantine")
    results = client.get(
        "/events/", params={"search": "cyber", "location": "constantine"}
    ).json()
    assert [e["id"] for e in results] == [target["id"]]


def test_list_events_no_filters_returns_all(client, create_event):
    create_event(title="Event A")
    create_event(title="Event B")
    assert len(client.get("/events/").json()) == 2


def test_list_events_empty_filters_are_ignored(client, create_event):
    create_event(title="Event A")
    create_event(title="Event B")
    results = client.get("/events/", params={"search": "", "location": ""}).json()
    assert len(results) == 2


# GET ONE

def test_get_event_returns_event(client, create_event):
    created = create_event()
    response = client.get(f"/events/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_event_not_found(client):
    response = client.get("/events/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Event not found."}


def test_get_event_picks_the_right_one(client, create_event):
    first = create_event(title="First Event")
    second = create_event(title="Second Event")
    assert client.get(f"/events/{second['id']}").json()["title"] == "Second Event"
    assert client.get(f"/events/{first['id']}").json()["title"] == "First Event"


def test_get_event_invalid_id_type(client):
    assert client.get("/events/abc").status_code == 422


# UPDATE

def test_update_event_changes_all_fields(client, create_event):
    created = create_event()
    new_data = {
        "title": "Updated Title",
        "description": "New description",
        "date": "2099-12-31",
        "location": "Oran",
        "capacity": 250,
    }
    response = client.put(f"/events/{created['id']}", json=new_data)
    assert response.status_code == 200
    assert response.json() == {"id": created["id"], **new_data}

    fetched = client.get(f"/events/{created['id']}").json()
    assert fetched == {"id": created["id"], **new_data}


def test_update_event_only_touches_target(client, create_event, sample_event_dict):
    first = create_event(title="First Event")
    second = create_event(title="Second Event")
    client.put(
        f"/events/{first['id']}", json={**sample_event_dict, "title": "Changed"}
    )
    assert client.get(f"/events/{second['id']}").json()["title"] == "Second Event"


def test_update_event_not_found(client, sample_event_dict):
    response = client.put("/events/999999", json=sample_event_dict)
    assert response.status_code == 404
    assert response.json() == {"detail": "Event not found."}


def test_update_event_not_found_takes_precedence_over_past_date(client, sample_event_dict):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = client.put(
        "/events/999999", json={**sample_event_dict, "date": yesterday}
    )
    assert response.status_code == 404


def test_update_event_past_date_rejected(client, create_event, sample_event_dict):
    created = create_event()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = client.put(
        f"/events/{created['id']}",
        json={**sample_event_dict, "title": "Should Not Save", "date": yesterday},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Event date cannot be in the past."}
    assert client.get(f"/events/{created['id']}").json() == created


def test_update_event_today_allowed(client, create_event, sample_event_dict):
    created = create_event()
    today = date.today().isoformat()
    response = client.put(
        f"/events/{created['id']}", json={**sample_event_dict, "date": today}
    )
    assert response.status_code == 200
    assert response.json()["date"] == today


def test_update_event_invalid_payload(client, create_event, sample_event_dict):
    created = create_event()
    response = client.put(
        f"/events/{created['id']}", json={**sample_event_dict, "capacity": 10001}
    )
    assert response.status_code == 422


# DELETE

def test_delete_event(client, create_event):
    created = create_event()
    response = client.delete(f"/events/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/events/{created['id']}").status_code == 404
    assert client.get("/events/").json() == []


def test_delete_event_not_found(client):
    response = client.delete("/events/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Event not found."}


def test_delete_event_keeps_others(client, create_event):
    first = create_event(title="First Event")
    second = create_event(title="Second Event")
    client.delete(f"/events/{first['id']}")
    remaining = client.get("/events/").json()
    assert [e["id"] for e in remaining] == [second["id"]]


def test_delete_twice_second_is_404(client, create_event):
    created = create_event()
    assert client.delete(f"/events/{created['id']}").status_code == 204
    assert client.delete(f"/events/{created['id']}").status_code == 404


# MODELS: TABLES AND COLUMNS

def test_table_names():
    assert Event.__tablename__ == "events"
    assert Participant.__tablename__ == "participants"
    assert Registration.__tablename__ == "registrations"


def test_event_columns():
    c = Event.__table__.c
    assert c.id.primary_key and c.id.index
    assert not c.title.nullable and c.title.type.length == 100
    assert c.description.nullable
    assert not c.date.nullable
    assert not c.location.nullable and c.location.type.length == 100
    assert not c.capacity.nullable


def test_participant_columns():
    c = Participant.__table__.c
    assert c.id.primary_key and c.id.index
    assert not c.name.nullable and c.name.type.length == 100
    assert not c.email.nullable and c.email.type.length == 150
    assert c.email.unique and c.email.index


def test_registration_columns_and_foreign_keys():
    c = Registration.__table__.c
    assert c.id.primary_key and c.id.index
    assert not c.event_id.nullable
    assert not c.participant_id.nullable
    assert {fk.target_fullname for fk in c.event_id.foreign_keys} == {"events.id"}
    assert {fk.target_fullname for fk in c.participant_id.foreign_keys} == {"participants.id"}


def test_registration_unique_constraint():
    constraints = [
        c for c in Registration.__table__.constraints
        if c.name == "uq_event_participant"
    ]
    assert len(constraints) == 1
    assert [col.name for col in constraints[0].columns] == ["event_id", "participant_id"]


# MODELS: RELATIONSHIPS

def test_relationships():
    ev = Event.registrations.property
    pa = Participant.registrations.property
    rg_e = Registration.event.property
    rg_p = Registration.participant.property

    assert ev.back_populates == "event"
    assert pa.back_populates == "participant"
    assert rg_e.back_populates == "registrations"
    assert rg_p.back_populates == "registrations"
    assert ev.mapper.class_ is Registration
    assert pa.mapper.class_ is Registration
    assert rg_e.mapper.class_ is Event
    assert rg_p.mapper.class_ is Participant

    for rel in (ev, pa):
        assert rel.cascade.delete
        assert rel.cascade.delete_orphan


# SCHEMAS

@pytest.mark.parametrize("title,ok", [("AB", False), ("ABC", True), ("A" * 100, True), ("A" * 101, False)])
def test_title_bounds(sample_event_dict, title, ok):
    data = {**sample_event_dict, "title": title}
    if ok:
        assert EventCreate(**data).title == title
    else:
        with pytest.raises(ValidationError):
            EventCreate(**data)


@pytest.mark.parametrize("location,ok", [("X", False), ("XY", True), ("L" * 100, True), ("L" * 101, False)])
def test_location_bounds(sample_event_dict, location, ok):
    data = {**sample_event_dict, "location": location}
    if ok:
        assert EventCreate(**data).location == location
    else:
        with pytest.raises(ValidationError):
            EventCreate(**data)


@pytest.mark.parametrize("name,ok", [("A", False), ("Al", True), ("N" * 100, True), ("N" * 101, False)])
def test_participant_name_bounds(sample_participant_dict, name, ok):
    data = {**sample_participant_dict, "name": name}
    if ok:
        assert ParticipantCreate(**data).name == name
    else:
        with pytest.raises(ValidationError):
            ParticipantCreate(**data)


@pytest.mark.parametrize("email", ["abc", "a@", "@b.com", "a@b", "a b@c.com", ""])
def test_participant_invalid_email(sample_participant_dict, email):
    with pytest.raises(ValidationError):
        ParticipantCreate(**{**sample_participant_dict, "email": email})


def test_from_attributes_enabled():
    assert EventSchema.model_config["from_attributes"] is True
    assert ParticipantSchema.model_config["from_attributes"] is True
    assert RegistrationSchema.model_config["from_attributes"] is True


def test_response_schemas_require_id(sample_event_dict, sample_participant_dict):
    with pytest.raises(ValidationError):
        EventSchema(**sample_event_dict)
    with pytest.raises(ValidationError):
        ParticipantSchema(**sample_participant_dict)
    with pytest.raises(ValidationError):
        RegistrationSchema(id=1, event_id=1)
