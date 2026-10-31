"""Add provider availability and booking responses.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind=op.get_bind()
    inspector=sa.inspect(bind)

    if bind.dialect.name=="postgresql":
        op.execute("ALTER TYPE bookingstatus ADD VALUE IF NOT EXISTS 'REJECTED'")

    booking_columns={column["name"] for column in inspector.get_columns("booking")}
    if "provider_response_note" not in booking_columns:
        op.add_column("booking",sa.Column("provider_response_note",sa.Text(),nullable=True))
    if "responded_at" not in booking_columns:
        op.add_column("booking",sa.Column("responded_at",sa.DateTime(),nullable=True))

    inspector=sa.inspect(bind)
    if not inspector.has_table("provider_availability"):
        op.create_table(
            "provider_availability",
            sa.Column("id",sa.Integer(),primary_key=True),
            sa.Column("provider_id",sa.Integer(),sa.ForeignKey("provider.id"),nullable=False),
            sa.Column("availability_date",sa.Date(),nullable=False),
            sa.Column("available",sa.Boolean(),nullable=False,server_default=sa.false()),
            sa.Column("note",sa.String(length=500),nullable=True),
            sa.Column("updated_at",sa.DateTime(),nullable=False,server_default=sa.func.now()),
            sa.UniqueConstraint("provider_id","availability_date",name="uq_provider_availability_date"),
        )
        op.create_index("ix_provider_availability_availability_date","provider_availability",["availability_date"])


def downgrade() -> None:
    bind=op.get_bind()
    inspector=sa.inspect(bind)
    if inspector.has_table("provider_availability"):
        op.drop_index("ix_provider_availability_availability_date",table_name="provider_availability")
        op.drop_table("provider_availability")
    booking_columns={column["name"] for column in sa.inspect(bind).get_columns("booking")}
    if "responded_at" in booking_columns:op.drop_column("booking","responded_at")
    if "provider_response_note" in booking_columns:op.drop_column("booking","provider_response_note")
    # PostgreSQL enum values are intentionally retained because removing one
    # requires rebuilding the type and may invalidate historical rows.
