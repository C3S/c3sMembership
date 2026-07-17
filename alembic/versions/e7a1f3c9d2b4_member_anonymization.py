"""Member anonymization

Adds the members.anonymized timestamp which records when a dataset was
anonymized (and thereby serves as the "is anonymized" flag) and makes
members.date_of_birth nullable so that anonymization can null it instead
of writing a fake sentinel date.

Revision ID: e7a1f3c9d2b4
Revises: d1a2b3c4e5f6
Create Date: 2026-07-17 18:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = 'e7a1f3c9d2b4'
down_revision = 'd1a2b3c4e5f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'members',
        sa.Column('anonymized', sa.DateTime(), nullable=True))
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column(
            'date_of_birth',
            existing_type=sa.Date(),
            nullable=True)


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column(
            'date_of_birth',
            existing_type=sa.Date(),
            nullable=False)
        batch_op.drop_column('anonymized')
