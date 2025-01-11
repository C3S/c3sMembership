"""Dues 2025

Revision ID: b967897092fc
Revises: 5ff1183c258b
Create Date: 2024-12-30 13:27:07.499401

"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types
from sqlalchemy.orm import Session

# revision identifiers, used by Alembic.
revision = 'b967897092fc'
down_revision = '5ff1183c258b'



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
        'dues25invoices', sa.Column('id', sa.Integer(), nullable=False),
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
            sa.Column('dues25_amount',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues25_amount_paid',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues25_amount_reduced',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues25_balance',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues25_balanced',
                      sa.Boolean(),
                      nullable=True,
                      default=True))
        batch_op.add_column(
            sa.Column('dues25_invoice',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues25_invoice_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues25_invoice_no', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('dues25_paid',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues25_paid_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues25_reduced',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues25_start', sa.Unicode(length=255), nullable=True))
        batch_op.add_column(
            sa.Column('dues25_token', sa.Unicode(length=10), nullable=True))

    # Problems with default values, so set explicitly
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute("""
        update
            members
        set
            dues25_amount = '0.0',
            dues25_amount_paid = '0.0',
            dues25_amount_reduced = '0.0',
            dues25_balance = '0.0',
            dues25_balanced = 1,
            dues25_invoice = 0,
            dues25_paid = 0,
            dues25_reduced = 0
    """)
    session.flush()
    session.commit()

def downgrade():
    with op.batch_alter_table('members', schema=None) as batch_op:
        batch_op.drop_column('dues25_token')
        batch_op.drop_column('dues25_start')
        batch_op.drop_column('dues25_reduced')
        batch_op.drop_column('dues25_paid_date')
        batch_op.drop_column('dues25_paid')
        batch_op.drop_column('dues25_invoice_no')
        batch_op.drop_column('dues25_invoice_date')
        batch_op.drop_column('dues25_invoice')
        batch_op.drop_column('dues25_balanced')
        batch_op.drop_column('dues25_balance')
        batch_op.drop_column('dues25_amount_reduced')
        batch_op.drop_column('dues25_amount_paid')
        batch_op.drop_column('dues25_amount')

    op.drop_table('dues25invoices')
