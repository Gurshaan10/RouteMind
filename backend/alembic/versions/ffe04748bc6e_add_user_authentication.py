"""add_user_authentication

Revision ID: ffe04748bc6e
Revises: 631d33b60e28
Create Date: 2026-01-12 15:48:30.763366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffe04748bc6e'
down_revision: Union[str, None] = '631d33b60e28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('google_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)

    # Add user_id to saved_itineraries
    op.add_column('saved_itineraries', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_saved_itineraries_user_id'), 'saved_itineraries', ['user_id'], unique=False)
    op.create_foreign_key('fk_saved_itineraries_user_id', 'saved_itineraries', 'users', ['user_id'], ['id'])

    # Add user_id to reviews
    op.add_column('reviews', sa.Column('user_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)
    op.create_foreign_key('fk_reviews_user_id', 'reviews', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    # Remove user_id from reviews
    op.drop_constraint('fk_reviews_user_id', 'reviews', type_='foreignkey')
    op.drop_index(op.f('ix_reviews_user_id'), table_name='reviews')
    op.drop_column('reviews', 'user_id')

    # Remove user_id from saved_itineraries
    op.drop_constraint('fk_saved_itineraries_user_id', 'saved_itineraries', type_='foreignkey')
    op.drop_index(op.f('ix_saved_itineraries_user_id'), table_name='saved_itineraries')
    op.drop_column('saved_itineraries', 'user_id')

    # Drop users table
    op.drop_index(op.f('ix_users_google_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
