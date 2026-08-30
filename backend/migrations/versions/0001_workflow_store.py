"""Create workflow, event, and artifact store tables.

Revision ID: 0001_workflow_store
Revises:
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_workflow_store"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("run_id", sa.String(length=64), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("case_id", sa.String(length=96), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("state", sa.String(length=48), nullable=False),
        sa.Column("fixture_mode", sa.Boolean(), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("config_hash", sa.String(length=64), nullable=False),
        sa.Column("stage_attempt", sa.Integer(), nullable=False),
        sa.Column("lease_owner", sa.String(length=128)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "run_events",
        sa.Column("event_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=48), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("evidence_ids_json", sa.Text(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "sequence", name="uq_run_events_sequence"),
    )
    op.create_index("ix_run_events_run_id", "run_events", ["run_id"])
    op.create_table(
        "artifacts",
        sa.Column("sha256", sa.String(length=64), primary_key=True),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "run_artifacts",
        sa.Column("run_artifact_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.String(length=64), sa.ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("logical_name", sa.String(length=96), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), sa.ForeignKey("artifacts.sha256"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "logical_name", name="uq_run_artifact_name"),
    )
    op.create_index("ix_run_artifacts_run_id", "run_artifacts", ["run_id"])


def downgrade() -> None:
    op.drop_table("run_artifacts")
    op.drop_table("artifacts")
    op.drop_table("run_events")
    op.drop_table("runs")
