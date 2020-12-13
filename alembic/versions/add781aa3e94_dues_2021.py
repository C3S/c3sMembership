"""Dues 2021

Revision ID: add781aa3e94
Revises: aa9364419026
Create Date: 2020-12-13 20:03:58.707479
"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types

# revision identifiers, used by Alembic.
revision = 'add781aa3e94'
down_revision = 'aa9364419026'


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


def upgrade():
    op.create_table(
        'dues21invoices', sa.Column('id', sa.Integer(), nullable=False),
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

    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('dues21_amount',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues21_amount_paid',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues21_amount_reduced',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues21_balance',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues21_balanced',
                      sa.Boolean(),
                      nullable=True,
                      default=True))
        batch_op.add_column(
            sa.Column('dues21_invoice',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues21_invoice_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues21_invoice_no', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('dues21_paid',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues21_paid_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues21_reduced',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues21_start', sa.Unicode(length=255), nullable=True))
        batch_op.add_column(
            sa.Column('dues21_token', sa.Unicode(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.drop_column('dues21_token')
        batch_op.drop_column('dues21_start')
        batch_op.drop_column('dues21_reduced')
        batch_op.drop_column('dues21_paid_date')
        batch_op.drop_column('dues21_paid')
        batch_op.drop_column('dues21_invoice_no')
        batch_op.drop_column('dues21_invoice_date')
        batch_op.drop_column('dues21_invoice')
        batch_op.drop_column('dues21_balanced')
        batch_op.drop_column('dues21_balance')
        batch_op.drop_column('dues21_amount_reduced')
        batch_op.drop_column('dues21_amount_paid')
        batch_op.drop_column('dues21_amount')

    op.drop_table('dues21invoices')
