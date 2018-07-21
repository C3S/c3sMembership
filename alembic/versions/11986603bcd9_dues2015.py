"""dues2015

Revision ID: 11986603bcd9
Revises: 3ca29da20ee4
Create Date: 2015-09-24 19:38:58.037063

"""

# revision identifiers, used by Alembic.
revision = '11986603bcd9'
down_revision = '3ca29da20ee4'

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
from sqlalchemy import update
from sqlalchemy.orm import Session
import sqlalchemy.types as types

from c3smembership.data.model.base.c3smember import C3sMember



class SqliteDecimal(types.TypeDecorator):
    """
    Type decorator for persisting Decimal (currency values)

    TODO: Use standard SQLAlchemy Decimal
    when a database is used which supports it.
    """
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        else:
            return None

    def process_result_value(self, value, dialect):
        if value is not None and value != '':
            return Decimal(value)
        else:
            return None


DatabaseDecimal = SqliteDecimal


def upgrade():
    # schema migration
    op.create_table('dues15invoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('invoice_no', sa.Integer(), nullable=True),
    sa.Column('invoice_no_string', sa.Unicode(length=255), nullable=True),
    sa.Column('invoice_date', sa.DateTime(), nullable=True),
    sa.Column('invoice_amount', DatabaseDecimal(length=12, collation=2), nullable=True),
    sa.Column('is_cancelled', sa.Boolean(), nullable=True),
    sa.Column('cancelled_date', sa.DateTime(), nullable=True),
    sa.Column('is_reversal', sa.Boolean(), nullable=True),
    sa.Column('is_altered', sa.Boolean(), nullable=True),
    sa.Column('member_id', sa.Integer(), nullable=True),
    sa.Column('membership_no', sa.Integer(), nullable=True),
    sa.Column('email', sa.Unicode(length=255), nullable=True),
    sa.Column('token', sa.Unicode(length=255), nullable=True),
    sa.Column('preceding_invoice_no', sa.Integer(), nullable=True),
    sa.Column('succeeding_invoice_no', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('invoice_no'),
    sa.UniqueConstraint('invoice_no_string')
    )
    op.add_column(u'members', sa.Column('dues15_amount', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column(u'members', sa.Column('dues15_amount_paid', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column(u'members', sa.Column('dues15_amount_reduced', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column(u'members', sa.Column('dues15_balance', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column(u'members', sa.Column('dues15_balanced', sa.Boolean(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_invoice', sa.Boolean(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_invoice_date', sa.DateTime(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_invoice_no', sa.Integer(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_paid', sa.Boolean(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_paid_date', sa.DateTime(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_reduced', sa.Boolean(), nullable=True))
    op.add_column(u'members', sa.Column('dues15_start', sa.Unicode(length=255), nullable=True))
    op.add_column(u'members', sa.Column('dues15_token', sa.Unicode(length=10), nullable=True))

    # data migration
    bind = op.get_bind()
    session = Session(bind=bind)
    # set default values for existing data
    session.execute(update(C3sMember).values(
        dues15_invoice=False,
        dues15_amount=Decimal('NaN'),
        dues15_amount_reduced=Decimal('NaN'),
        dues15_balance=Decimal('0'),
        dues15_balanced=True,
        dues15_paid=False,
        dues15_amount_paid=Decimal('0')))
    session.flush()
    session.commit()




def downgrade():
    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('dues15_token')
        batch_op.drop_column('dues15_start')
        batch_op.drop_column('dues15_reduced')
        batch_op.drop_column('dues15_paid_date')
        batch_op.drop_column('dues15_paid')
        batch_op.drop_column('dues15_invoice_no')
        batch_op.drop_column('dues15_invoice_date')
        batch_op.drop_column('dues15_invoice')
        batch_op.drop_column('dues15_balanced')
        batch_op.drop_column('dues15_balance')
        batch_op.drop_column('dues15_amount_reduced')
        batch_op.drop_column('dues15_amount_paid')
        batch_op.drop_column('dues15_amount')

    op.drop_table('dues15invoices')
