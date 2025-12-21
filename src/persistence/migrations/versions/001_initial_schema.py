"""Initial Baby MARS schema

Revision ID: 001
Revises:
Create Date: 2024-12-21

Creates the initial database schema for Baby MARS:
- beliefs: Stores belief graph nodes
- memories: Episodic and procedural memory
- feedback_events: Immutable audit log
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Beliefs table
    op.create_table(
        'beliefs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('belief_id', sa.String(255), nullable=False),
        sa.Column('org_id', sa.String(255), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('strength', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('context_key', sa.String(255), nullable=False, server_default='*|*|*'),
        sa.Column('context_states', sa.JSON(), nullable=True),
        sa.Column('immutable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'belief_id', name='uix_org_belief')
    )
    op.create_index('ix_beliefs_org_id', 'beliefs', ['org_id'])
    op.create_index('ix_beliefs_category', 'beliefs', ['category'])
    op.create_index('ix_beliefs_context_key', 'beliefs', ['context_key'])

    # Memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('memory_id', sa.String(255), nullable=False),
        sa.Column('org_id', sa.String(255), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False),  # episodic, procedural
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('outcome', sa.String(50), nullable=True),  # success, failure
        sa.Column('emotional_intensity', sa.Float(), nullable=True),
        sa.Column('peak_moment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('related_beliefs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', 'memory_id', name='uix_org_memory')
    )
    op.create_index('ix_memories_org_id', 'memories', ['org_id'])
    op.create_index('ix_memories_memory_type', 'memories', ['memory_type'])
    op.create_index('ix_memories_outcome', 'memories', ['outcome'])

    # Feedback events table (immutable audit log)
    op.create_table(
        'feedback_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('org_id', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('turn_id', sa.String(255), nullable=True),
        sa.Column('thread_id', sa.String(255), nullable=True),
        sa.Column('belief_updates', sa.JSON(), nullable=True),
        sa.Column('outcome', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),  # user, system, llm
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feedback_events_org_id', 'feedback_events', ['org_id'])
    op.create_index('ix_feedback_events_event_type', 'feedback_events', ['event_type'])
    op.create_index('ix_feedback_events_turn_id', 'feedback_events', ['turn_id'])
    op.create_index('ix_feedback_events_created_at', 'feedback_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('feedback_events')
    op.drop_table('memories')
    op.drop_table('beliefs')
