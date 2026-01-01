"""Dues 2026

Revision ID: c5d3e9a8f2b1
Revises: b967897092fc
Create Date: 2025-12-27 12:00:00.000000

"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'c5d3e9a8f2b1'
down_revision = 'b967897092fc'



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


def upgrade():
    op.create_table(
        'dues26invoices', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_no', sa.Integer(), nullable=True),
        sa.Column('invoice_no_string', sa.Unicode(length=255), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('invoice_amount',
                  SqliteDecimal(length=12, collation=2),
                  nullable=True),
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
        sa.PrimaryKeyConstraint('id'), sa.UniqueConstraint('invoice_no'),
        sa.UniqueConstraint('invoice_no_string'))

    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('dues26_amount',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues26_amount_paid',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues26_amount_reduced',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues26_balance',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues26_balanced',
                      sa.Boolean(),
                      nullable=True,
                      default=True))
        batch_op.add_column(
            sa.Column('dues26_invoice',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues26_invoice_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues26_invoice_no', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('dues26_paid',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues26_paid_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues26_reduced',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues26_start', sa.Unicode(length=255), nullable=True))
        batch_op.add_column(
            sa.Column('dues26_token', sa.Unicode(length=10), nullable=True))

    # Problems with default values, so set explicitly
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute("""
        update
            members
        set
            dues26_amount = '0.0',
            dues26_amount_paid = '0.0',
            dues26_amount_reduced = '0.0',
            dues26_balance = '0.0',
            dues26_balanced = 1,
            dues26_invoice = 0,
            dues26_paid = 0,
            dues26_reduced = 0
    """)
    session.flush()
    session.commit()

def downgrade():
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_column('dues26_token')
        batch_op.drop_column('dues26_start')
        batch_op.drop_column('dues26_reduced')
        batch_op.drop_column('dues26_paid_date')
        batch_op.drop_column('dues26_paid')
        batch_op.drop_column('dues26_invoice_no')
        batch_op.drop_column('dues26_invoice_date')
        batch_op.drop_column('dues26_invoice')
        batch_op.drop_column('dues26_balanced')
        batch_op.drop_column('dues26_balance')
        batch_op.drop_column('dues26_amount_reduced')
        batch_op.drop_column('dues26_amount_paid')
        batch_op.drop_column('dues26_amount')

    op.drop_table('dues26invoices')
