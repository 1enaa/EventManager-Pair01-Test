import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registers tables on Base)
from app.database import Base, get_db
from app.main import app


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


@pytest.fixture
def client():
    """TestClient wired to an isolated in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def global_environment_logger(request):
    print(f"\n[SETUP] Starting: {request.node.name}")
    yield
    print(f"\n[TEARDOWN] Finished: {request.node.name}")