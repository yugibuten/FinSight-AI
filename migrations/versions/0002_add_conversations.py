"""Add conversations and associate research turns.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("research_queries") as batch_op:
        batch_op.add_column(sa.Column("conversation_id", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("turn_index", sa.Integer(), nullable=True))
        batch_op.create_index("ix_research_queries_conversation_id", ["conversation_id"])
        batch_op.create_foreign_key(
            "fk_research_queries_conversation_id",
            "conversations",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("research_queries") as batch_op:
        batch_op.drop_constraint("fk_research_queries_conversation_id", type_="foreignkey")
        batch_op.drop_index("ix_research_queries_conversation_id")
        batch_op.drop_column("turn_index")
        batch_op.drop_column("conversation_id")
    op.drop_table("conversations")
