import pytest


@pytest.fixture
def sample_event_dict():
    return {
        "title": "Cybersecurity Workshop",
        "description": "A workshop about cybersecurity.",
        "date": "2099-11-15",
        "location": "Constantine",
        "capacity": 100,
    }


@pytest.fixture
def sample_participant_dict():
    return {
        "name": "Amine",
        "email": "amine@example.com",
    }


@pytest.fixture
def mock_event_store():
    store = []
    yield store
    store.clear()


@pytest.fixture
def prepopulated_event_store(mock_event_store):
    mock_event_store.extend([
        {
            "id": 1,
            "title": "Cybersecurity Workshop",
            "location": "Constantine",
            "capacity": 100,
        },
        {
            "id": 2,
            "title": "Python Training",
            "location": "Algiers",
            "capacity": 50,
        },
        {
            "id": 3,
            "title": "Advanced Cybersecurity",
            "location": "Constantine",
            "capacity": 200,
        },
    ])
    return mock_event_store


@pytest.fixture(autouse=True)
def global_environment_logger(request):
    print(f"\n[SETUP] Starting: {request.node.name}")
    yield
    print(f"\n[TEARDOWN] Finished: {request.node.name}")
