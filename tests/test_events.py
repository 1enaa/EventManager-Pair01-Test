import pytest
from fastapi import APIRouter
from pydantic import ValidationError

from app.event_utils import (
    filter_events_by_location,
    filter_events_by_title,
)
from app.routers.events import router
from app.schemas import EventCreate


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