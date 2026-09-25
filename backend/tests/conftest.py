import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Customer, Provider, Role, ServicePackage, UserAccount


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
        provider_user = UserAccount(email="provider@example.test", password_hash="test", role=Role.PROVIDER)
        customer_user = UserAccount(email="customer@example.test", password_hash="test", role=Role.CUSTOMER)
        db.add_all([provider_user, customer_user])
        db.flush()
        provider = Provider(user_id=provider_user.id, first_name="Maya", last_name="Patel", bio="Designer", rating=4.8, published=True, status="Approved")
        customer = Customer(user_id=customer_user.id, first_name="Jordan", last_name="Lee")
        db.add_all([provider, customer])
        db.flush()
        package = ServicePackage(provider_id=provider.id, category="Design", title="UX Review", description="Accessibility review", price=450, duration_days=7)
        db.add(package)
        db.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app)
