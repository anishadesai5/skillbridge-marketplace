"""Add customer notes and creation timestamp to booking requests.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Revision 0001 was created from SQLAlchemy metadata. The guards keep a
    # brand-new database and an already-running course database upgrade-safe.
    existing={column["name"] for column in sa.inspect(op.get_bind()).get_columns("booking")}
    if "customer_notes" not in existing:
        op.add_column("booking", sa.Column("customer_notes", sa.Text(), nullable=True))
    if "created_at" not in existing:
        op.add_column("booking",sa.Column("created_at",sa.DateTime(),server_default=sa.func.now(),nullable=False))


def downgrade() -> None:
    existing={column["name"] for column in sa.inspect(op.get_bind()).get_columns("booking")}
    if "created_at" in existing:op.drop_column("booking", "created_at")
    if "customer_notes" in existing:op.drop_column("booking", "customer_notes")
