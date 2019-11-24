"""Cleanup invitations

Revision ID: 57a76e578475
Revises: 9f0baac0c2
Create Date: 2019-02-12 20:54:58.587102

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '57a76e578475'
down_revision = '1638f269c5f5'


def upgrade():
    with op.batch_alter_table(
            u'GeneralAssemblyInvitation', schema=None) as batch_op:
        batch_op.alter_column(
            'sent',
            existing_type=sa.DATETIME(),
            nullable=False)
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.drop_column('email_invite_token_bcgv18_2')
        batch_op.drop_column('email_invite_flag_bcgv18_2')
        batch_op.drop_column('email_invite_date_bcgv18_2')


def downgrade():
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'email_invite_date_bcgv18_2', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column(
            'email_invite_flag_bcgv18_2', sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column(
            'email_invite_token_bcgv18_2',
            sa.VARCHAR(length=255),
            nullable=True))
    with op.batch_alter_table(
            u'GeneralAssemblyInvitation', schema=None) as batch_op:
        batch_op.alter_column(
            'sent',
            existing_type=sa.DATETIME(),
            nullable=True)
