from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.services import publish_provider


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(UserAccount.id).limit(1)):
            return

        provider_user = UserAccount(
            email="maya.provider@example.test",
            password_hash="demo-only-not-a-real-password",
            role=Role.PROVIDER,
        )
        customer_user = UserAccount(
            email="jordan.customer@example.test",
            password_hash="demo-only-not-a-real-password",
            role=Role.CUSTOMER,
        )
        db.add_all([provider_user, customer_user])
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
        db.add_all([provider, customer])
        db.flush()

        db.add(Credential(provider_id=provider.id, credential_type="Portfolio Review", document_url="https://example.test/credential", status="Verified"))
        db.add(ServicePackage(provider_id=provider.id, category="Design", title="Accessibility UX Review", description="A structured accessibility review with prioritized recommendations.", price=Decimal("450.00"), duration_days=7))
        db.flush()
        publish_provider(db, provider)
        db.commit()


if __name__ == "__main__":
    seed()
