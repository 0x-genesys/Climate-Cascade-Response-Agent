"""Add durable human review decisions.

Revision ID: 0002_human_reviews
Revises: 0001_workflow_store
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_human_reviews"
down_revision = "0001_workflow_store"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "action_reviews",
        sa.Column("review_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_id", sa.String(length=128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reviewer_id", sa.String(length=96), nullable=False),
        sa.Column("reviewer_role", sa.String(length=160), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("assumptions_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "action_id", "version", name="uq_action_review_version"),
    )
    op.create_index("ix_action_reviews_run_id", "action_reviews", ["run_id"])


def downgrade() -> None:
    op.drop_table("action_reviews")
