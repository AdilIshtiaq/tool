import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres@localhost:5432/nexcraft_salesos_test"
os.environ["API_KEY"] = "test-api-key"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app
from app import models  # noqa: F401  registers all tables on Base.metadata

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _block_real_smtp(monkeypatch):
    """Tests must never make a real outbound SMTP connection - backend/.env
    has real production credentials, and a test send to a fake address
    (owner@example.com, etc.) would be a real SMTP transaction against them.
    A test that wants to exercise real send_email()/EmailSendError behavior
    should monkeypatch this back within that test."""
    import app.services.outreach_execution as outreach_execution_module

    def _fake_send_email(**kwargs):
        return "Accepted by SMTP server for delivery (test double - no real SMTP call made)"

    monkeypatch.setattr(outreach_execution_module, "send_email", _fake_send_email)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, headers={"X-API-Key": os.environ["API_KEY"]}) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_lead(db_session):
    from app.models import Lead

    def _make(**overrides):
        defaults = dict(
            business_name="Test Business",
            category="Restaurant",
            city="Lahore",
            country="Pakistan",
            phone="0300 1234567",
            website="https://example.com",
            rating=4.5,
            review_count=100,
            source="google_places",
            source_id=f"test-{os.urandom(4).hex()}",
            status="new",
        )
        defaults.update(overrides)
        lead = Lead(**defaults)
        db_session.add(lead)
        db_session.commit()
        db_session.refresh(lead)
        return lead

    return _make
