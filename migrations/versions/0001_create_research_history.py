"""Create research history tables.

Revision ID: 0001
Revises:
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_queries",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("request_id", sa.String(length=80), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("response_type", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_cache_hit", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=60), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_queries_request_id", "research_queries", ["request_id"])
    op.create_index("ix_research_queries_status", "research_queries", ["status"])
    op.create_table(
        "research_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query_id", sa.String(length=40), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["research_queries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("query_id"),
    )
    op.create_index("ix_research_results_query_id", "research_results", ["query_id"])
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query_id", sa.String(length=40), nullable=False),
        sa.Column("tool_name", sa.String(length=80), nullable=False),
        sa.Column("arguments_json", sa.JSON(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["query_id"], ["research_queries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tool_executions_query_id", "tool_executions", ["query_id"])
    op.create_index("ix_tool_executions_tool_name", "tool_executions", ["tool_name"])


def downgrade() -> None:
    op.drop_index("ix_tool_executions_tool_name", table_name="tool_executions")
    op.drop_index("ix_tool_executions_query_id", table_name="tool_executions")
    op.drop_table("tool_executions")
    op.drop_index("ix_research_results_query_id", table_name="research_results")
    op.drop_table("research_results")
    op.drop_index("ix_research_queries_status", table_name="research_queries")
    op.drop_index("ix_research_queries_request_id", table_name="research_queries")
    op.drop_table("research_queries")
