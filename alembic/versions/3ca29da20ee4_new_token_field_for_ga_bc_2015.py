"""new token field for GA + BC 2015

Revision ID: 3ca29da20ee4
Revises: 2a6d1059c519
Create Date: 2015-05-20 13:30:51.280773

"""

# revision identifiers, used by Alembic.
revision = '3ca29da20ee4'
down_revision = '2a6d1059c519'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('members', sa.Column('email_invite_token_bcgv15', sa.Unicode(length=255), nullable=True))
    ### end Alembic commands ###


def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('email_invite_token_bcgv15')
