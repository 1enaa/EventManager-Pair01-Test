
from fastapi.testclient import TestClient


# Integration Test 1: Event Creation & Persistence Verification
def test_create_and_fetch_event_integration(client: TestClient):
    response = client.post("/events/", json={
        "title": "DevOps Integration Conf",
        "description": "Integration testing conference",
        "location": "Constantine",
        "date": "2099-12-01",
        "capacity": 200
    })

    assert response.status_code == 201

    event_id = response.json()["id"]

    get_response = client.get(f"/events/{event_id}")

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "DevOps Integration Conf"
    assert get_response.json()["location"] == "Constantine"


# Integration Test 2: Participant Registration Workflow
def test_register_participant_to_event_integration(client: TestClient):
    # 1. Create Event
    event_response = client.post("/events/", json={
        "title": "Cybersecurity Workshop",
        "description": "A cybersecurity training session",
        "location": "NTIC",
        "date": "2099-11-15",
        "capacity": 50
    })

    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    # 2. Create Participant
    participant_response = client.post("/participants/", json={
        "name": "Alice Dev",
        "email": "alice@example.com"
    })

    assert participant_response.status_code == 201
    participant_id = participant_response.json()["id"]

    # 3. Register Participant to Event
    registration_response = client.post(
        f"/events/{event_id}/register/{participant_id}"
    )

    assert registration_response.status_code == 201
    assert registration_response.json()["event_id"] == event_id
    assert registration_response.json()["participant_id"] == participant_id

    # 4. Verify Registration through Event Participants List
    list_response = client.get(
        f"/events/{event_id}/participants"
    )

    assert list_response.status_code == 200
    assert any(
        p["id"] == participant_id
        for p in list_response.json()
    )


# Integration Test 3: Registering to a Non-Existent Event
def test_register_non_existent_event_returns_404(client: TestClient):
    response = client.post("/events/9999/register/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found."


# Integration Test 4: Duplicate Participant Email
def test_duplicate_participant_email_returns_409(client: TestClient):
    participant_data = {
        "name": "Alice Dev",
        "email": "alice@example.com"
    }

    first_response = client.post(
        "/participants/",
        json=participant_data
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/participants/",
        json=participant_data
    )

    assert second_response.status_code == 409


# Integration Test 5: Duplicate Event Registration
def test_duplicate_registration_returns_409(client: TestClient):
    event_response = client.post("/events/", json={
        "title": "Testing Workshop",
        "description": "Testing duplicate registrations",
        "location": "Constantine",
        "date": "2099-12-01",
        "capacity": 10
    })

    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    participant_response = client.post("/participants/", json={
        "name": "Bob Dev",
        "email": "bob@example.com"
    })

    assert participant_response.status_code == 201
    participant_id = participant_response.json()["id"]

    first_registration = client.post(
        f"/events/{event_id}/register/{participant_id}"
    )

    assert first_registration.status_code == 201

    second_registration = client.post(
        f"/events/{event_id}/register/{participant_id}"
    )

    assert second_registration.status_code == 409


# Integration Test 6: Event Capacity Constraint
def test_registration_exceeding_event_capacity_returns_409(
    client: TestClient
):
    event_response = client.post("/events/", json={
        "title": "Limited Capacity Event",
        "description": "An event with only one available place",
        "location": "NTIC",
        "date": "2099-12-01",
        "capacity": 1
    })

    assert event_response.status_code == 201
    event_id = event_response.json()["id"]

    # Create two participants
    participant_ids = []

    for name, email in [
        ("Alice Dev", "alice@example.com"),
        ("Bob Dev", "bob@example.com")
    ]:
        response = client.post("/participants/", json={
            "name": name,
            "email": email
        })

        assert response.status_code == 201
        participant_ids.append(response.json()["id"])

    # First participant takes the only available place
    first_registration = client.post(
        f"/events/{event_id}/register/{participant_ids[0]}"
    )

    assert first_registration.status_code == 201

    # Second participant cannot register
    second_registration = client.post(
        f"/events/{event_id}/register/{participant_ids[1]}"
    )

    assert second_registration.status_code == 409
