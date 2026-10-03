import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Administrator, Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.security import hash_password


engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_db


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestingSession() as db:
        provider_user = UserAccount(email="provider@example.test", password_hash=hash_password("Provider123!"), role=Role.PROVIDER)
        customer_user = UserAccount(email="customer@example.test", password_hash=hash_password("Customer123!"), role=Role.CUSTOMER)
        admin_user = UserAccount(email="admin@example.test", password_hash=hash_password("Admin123!"), role=Role.ADMIN)
        db.add_all([provider_user, customer_user, admin_user])
        db.flush()
        provider = Provider(user_id=provider_user.id, first_name="Maya", last_name="Patel", bio="Designer", rating=4.8, published=True, status="Approved")
        customer = Customer(user_id=customer_user.id, first_name="Jordan", last_name="Lee")
        admin = Administrator(user_id=admin_user.id, name="Admin User")
        db.add_all([provider, customer, admin])
        db.flush()
        db.add(Credential(provider_id=provider.id, credential_type="Portfolio", document_url="https://example.test/credential", status="Verified"))
        package = ServicePackage(provider_id=provider.id, category="Design", title="UX Review", description="Accessibility review", price=450, duration_days=7)
        db.add(package)
        db.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def customer_headers(client):
    response = client.post("/auth/login", json={"email": "customer@example.test", "password": "Customer123!"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def provider_headers(client):
    response = client.post("/auth/login", json={"email": "provider@example.test", "password": "Provider123!"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client):
    response = client.post("/auth/login", json={"email": "admin@example.test", "password": "Admin123!"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
