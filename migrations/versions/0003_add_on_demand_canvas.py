"""Add persistent on-demand research canvases.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "canvases",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("conversation_id", sa.String(length=40), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id"),
    )
    op.create_index("ix_canvases_conversation_id", "canvases", ["conversation_id"])
    op.create_table(
        "canvas_operations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("canvas_id", sa.String(length=40), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("operations_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["canvas_id"], ["canvases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_canvas_operations_canvas_id", "canvas_operations", ["canvas_id"])


def downgrade() -> None:
    op.drop_index("ix_canvas_operations_canvas_id", table_name="canvas_operations")
    op.drop_table("canvas_operations")
    op.drop_index("ix_canvases_conversation_id", table_name="canvases")
    op.drop_table("canvases")
