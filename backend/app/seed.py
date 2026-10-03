from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import Administrator, Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.security import hash_password
from app.services import publish_provider


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(UserAccount.id).where(UserAccount.email == "admin@skillbridge.test")):
            return

        provider_user = UserAccount(
            email="maya.provider@example.test",
            password_hash=hash_password("Provider123!"),
            role=Role.PROVIDER,
        )
        customer_user = UserAccount(
            email="jordan.customer@example.test",
            password_hash=hash_password("Customer123!"),
            role=Role.CUSTOMER,
        )
        admin_user = UserAccount(
            email="admin@skillbridge.test",
            password_hash=hash_password("Admin123!"),
            role=Role.ADMIN,
        )
        db.add_all([provider_user, customer_user, admin_user])
        db.flush()

        provider = Provider(
            user_id=provider_user.id,
            first_name="Maya",
            last_name="Patel",
            bio="UX designer focused on accessible product experiences.",
            portfolio_url="https://example.test/maya",
            rating=Decimal("4.8"),
        )
        customer = Customer(
            user_id=customer_user.id,
            first_name="Jordan",
            last_name="Lee",
            phone="555-0100",
        )
        administrator = Administrator(user_id=admin_user.id, name="Avery Morgan", admin_role="PlatformAdmin")
        db.add_all([provider, customer, administrator])
        db.flush()

        db.add(Credential(provider_id=provider.id, credential_type="Portfolio Review", document_url="https://example.test/credential", status="Verified"))
        db.add_all([
            ServicePackage(provider_id=provider.id, category="Design", title="Accessibility UX Review", description="A structured accessibility review with prioritized recommendations.", price=Decimal("450.00"), duration_days=7),
            ServicePackage(provider_id=provider.id, category="Design", title="Landing Page Critique", description="A focused usability review for one landing page.", price=Decimal("175.00"), duration_days=3),
        ])
        db.flush()
        publish_provider(db, provider)
        db.commit()


if __name__ == "__main__":
    seed()
