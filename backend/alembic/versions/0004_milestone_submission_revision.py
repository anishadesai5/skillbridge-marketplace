"""Add milestone submission and revision details.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestone", sa.Column("submission_notes", sa.Text(), nullable=True))
    op.add_column("milestone", sa.Column("revision_reason", sa.Text(), nullable=True))
    op.add_column("milestone", sa.Column("submission_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("milestone", "submission_count")
    op.drop_column("milestone", "revision_reason")
    op.drop_column("milestone", "submission_notes")
