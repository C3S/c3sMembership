"""Dues 2016

Revision ID: 422952c27a95
Revises: b47056df26f0
Create Date: 2016-06-25 11:00:41.563828

"""

# revision identifiers, used by Alembic.
revision = '422952c27a95'
down_revision = 'b47056df26f0'

from datetime import (
    datetime,
)
from decimal import Decimal

from alembic import op

from sqlalchemy.sql import func
from sqlalchemy.orm import (
    Session
)
import sqlalchemy as sa
import sqlalchemy.types as types


class SqliteDecimal(types.TypeDecorator):
    """
    Type decorator for persisting Decimal (currency values)

    TODO: Use standard SQLAlchemy Decimal
    when a database is used which supports it.
    """
    impl = types.String
    cache_ok = False

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
    op.create_table('dues16invoices',
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
    op.add_column('members', sa.Column('dues16_amount', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column('members', sa.Column('dues16_amount_paid', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column('members', sa.Column('dues16_amount_reduced', DatabaseDecimal(length=12, collation=2), nullable=True))
    op.add_column('members', sa.Column('dues16_balance', DatabaseDecimal(length=12, collation=2), nullable=True, default=Decimal('0.0')))
    op.add_column('members', sa.Column('dues16_balanced', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('dues16_invoice', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('dues16_invoice_date', sa.DateTime(), nullable=True))
    op.add_column('members', sa.Column('dues16_invoice_no', sa.Integer(), nullable=True))
    op.add_column('members', sa.Column('dues16_paid', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('dues16_paid_date', sa.DateTime(), nullable=True))
    op.add_column('members', sa.Column('dues16_reduced', sa.Boolean(), nullable=True))
    op.add_column('members', sa.Column('dues16_start', sa.Unicode(length=255), nullable=True))
    op.add_column('members', sa.Column('dues16_token', sa.Unicode(length=10), nullable=True))

    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute("""
        update
            members
        set
            dues16_invoice = 0
            ,
            dues16_amount = 'NaN'
            ,
            dues16_reduced = 0
            ,
            dues16_amount_reduced = 'NaN'
            ,
            dues16_balance = '0'
            ,
            dues16_balanced = 1
            ,
            dues16_paid = 0
            ,
            dues16_amount_paid = '0'
        """
    )
    session.flush()
    session.commit()


def downgrade():
    op.drop_table('dues16invoices')

    with op.batch_alter_table('members') as batch_op:
        batch_op.drop_column('dues16_token')
        batch_op.drop_column('dues16_start')
        batch_op.drop_column('dues16_reduced')
        batch_op.drop_column('dues16_paid_date')
        batch_op.drop_column('dues16_paid')
        batch_op.drop_column('dues16_invoice_no')
        batch_op.drop_column('dues16_invoice_date')
        batch_op.drop_column('dues16_invoice')
        batch_op.drop_column('dues16_balanced')
        batch_op.drop_column('dues16_balance')
        batch_op.drop_column('dues16_amount_reduced')
        batch_op.drop_column('dues16_amount_paid')
        batch_op.drop_column('dues16_amount')
