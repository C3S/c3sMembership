"""fields for bc & gv 2016

Revision ID: b47056df26f0
Revises: 1de26724691f
Create Date: 2016-02-16 19:03:49.889655

"""

# revision identifiers, used by Alembic.
revision = 'b47056df26f0'
down_revision = '1de26724691f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('members', sa.Column('email_invite_date_bcgv16', sa.DateTime(), nullable=True))
    op.add_column('members', sa.Column('email_invite_flag_bcgv16', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('email_invite_token_bcgv16', sa.Unicode(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('email_invite_token_bcgv16')
        batch_op.drop_column('email_invite_flag_bcgv16')
        batch_op.drop_column('email_invite_date_bcgv16')
