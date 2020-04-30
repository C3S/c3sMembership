"""General assembly invitation text

Revision ID: aa9364419026
Revises: c77d27c6dc1e
Create Date: 2020-04-30 20:30:40.067724

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aa9364419026'
down_revision = 'c77d27c6dc1e'


def upgrade():
    op.add_column(
        'GeneralAssembly',
        sa.Column('invitation_subject_en', sa.Unicode(1000), nullable=True))
    op.add_column(
        'GeneralAssembly',
        sa.Column('invitation_text_en', sa.Unicode(1000000), nullable=True))
    op.add_column(
        'GeneralAssembly',
        sa.Column('invitation_subject_de', sa.Unicode(1000), nullable=True))
    op.add_column(
        'GeneralAssembly',
        sa.Column('invitation_text_de', sa.Unicode(1000000), nullable=True))


def downgrade():
    with op.batch_alter_table('GeneralAssembly') as batch_op:
        batch_op.drop_column('invitation_subject_en')
        batch_op.drop_column('invitation_text_en')
        batch_op.drop_column('invitation_subject_de')
        batch_op.drop_column('invitation_text_de')
