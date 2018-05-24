"""Add member privacy consent

Revision ID: d4c59e012aa
Revises: 34c421bb0d0c
Create Date: 2018-05-24 20:41:56.219669

"""

# revision identifiers, used by Alembic.
revision = 'd4c59e012aa'
down_revision = '34c421bb0d0c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'members',
        sa.Column('privacy_consent', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('privacy_consent')
