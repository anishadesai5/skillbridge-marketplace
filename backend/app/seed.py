from datetime import date
from decimal import Decimal
import secrets

from sqlalchemy import select

from app.db import Base, SessionLocal, engine
from app.models import Administrator, Credential, Customer, Provider, Role, ServicePackage, UserAccount
from app.security import hash_password
from app.services import publish_provider


def seed() -> None:
    demo_password=secrets.token_urlsafe(24)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(UserAccount.id).where(UserAccount.email == "admin@skillbridge.test")):
            return

        provider_user = UserAccount(
            email="maya.provider@example.test",
            password_hash=hash_password(demo_password),
            role=Role.PROVIDER,
        )
        customer_user = UserAccount(
            email="jordan.customer@example.test",
            password_hash=hash_password(demo_password),
            role=Role.CUSTOMER,
        )
        admin_user = UserAccount(
            email="admin@skillbridge.test",
            password_hash=hash_password(demo_password),
            role=Role.ADMIN,
        )
        second_provider_user = UserAccount(
            email="sam.provider@example.test",
            password_hash=hash_password(demo_password),
            role=Role.PROVIDER,
        )
        pending_provider_user = UserAccount(
            email="pending.provider@example.test",
            password_hash=hash_password(demo_password),
            role=Role.PROVIDER,
        )
        db.add_all([provider_user, second_provider_user, pending_provider_user, customer_user, admin_user])
        db.flush()

        provider = Provider(
            user_id=provider_user.id,
            first_name="Maya",
            last_name="Patel",
            bio="UX designer focused on accessible product experiences.",
            portfolio_url="https://example.test/maya",
            rating=Decimal("4.8"),
        )
        second_provider = Provider(
            user_id=second_provider_user.id,
            first_name="Sam",
            last_name="Rivera",
            bio="Career coach helping technology professionals prepare for interviews.",
            portfolio_url="https://example.test/sam",
            rating=Decimal("4.6"),
        )
        pending_provider = Provider(
            user_id=pending_provider_user.id,
            first_name="Taylor",
            last_name="Pending",
            bio="This pending profile must not appear in public search results.",
            rating=Decimal("5.0"),
            status="Pending",
            published=False,
        )
        customer = Customer(
            user_id=customer_user.id,
            first_name="Jordan",
            last_name="Lee",
            phone="555-0100",
        )
        administrator = Administrator(user_id=admin_user.id, name="Avery Morgan", admin_role="PlatformAdmin")
        db.add_all([provider, second_provider, pending_provider, customer, administrator])
        db.flush()

        db.add(Credential(provider_id=provider.id, credential_type="Portfolio Review", document_url="https://example.test/credential", status="Verified"))
        db.add(Credential(provider_id=second_provider.id, credential_type="Coaching Certificate", document_url="https://example.test/coaching-certificate", status="Verified"))
        db.add_all([
            ServicePackage(provider_id=provider.id, category="Design", title="Accessibility UX Review", description="A structured accessibility review with prioritized recommendations.", price=Decimal("450.00"), duration_days=7),
            ServicePackage(provider_id=provider.id, category="Design", title="Landing Page Critique", description="A focused usability review for one landing page.", price=Decimal("175.00"), duration_days=3),
            ServicePackage(provider_id=second_provider.id, category="Career", title="Technical Interview Coaching", description="A mock interview and personalized feedback session.", price=Decimal("225.00"), duration_days=2),
            ServicePackage(provider_id=second_provider.id, category="Career", title="Resume Review", description="A detailed review of one technical resume.", price=Decimal("95.00"), duration_days=2),
            ServicePackage(provider_id=pending_provider.id, category="Design", title="Hidden Pending Service", description="This package is intentionally excluded from search.", price=Decimal("50.00"), duration_days=1),
        ])
        db.flush()
        publish_provider(db, provider)
        publish_provider(db, second_provider)
        db.commit()


if __name__ == "__main__":
    seed()
