"""Dues 2023

Revision ID: 5432ac905cd2
Revises: baf9bc4aa1ad
Create Date: 2022-12-18 22:09:36.903720

"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types

# revision identifiers, used by Alembic.
revision = '5432ac905cd2'
down_revision = 'baf9bc4aa1ad'


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
        'dues23invoices', sa.Column('id', sa.Integer(), nullable=False),
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
            sa.Column('dues23_amount',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues23_amount_paid',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues23_amount_reduced',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues23_balance',
                      SqliteDecimal(length=12, collation=2),
                      nullable=True,
                      default=Decimal('0.0')))
        batch_op.add_column(
            sa.Column('dues23_balanced',
                      sa.Boolean(),
                      nullable=True,
                      default=True))
        batch_op.add_column(
            sa.Column('dues23_invoice',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues23_invoice_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues23_invoice_no', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('dues23_paid',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues23_paid_date', sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column('dues23_reduced',
                      sa.Boolean(),
                      nullable=True,
                      default=False))
        batch_op.add_column(
            sa.Column('dues23_start', sa.Unicode(length=255), nullable=True))
        batch_op.add_column(
            sa.Column('dues23_token', sa.Unicode(length=10), nullable=True))


def downgrade():
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.drop_column('dues23_token')
        batch_op.drop_column('dues23_start')
        batch_op.drop_column('dues23_reduced')
        batch_op.drop_column('dues23_paid_date')
        batch_op.drop_column('dues23_paid')
        batch_op.drop_column('dues23_invoice_no')
        batch_op.drop_column('dues23_invoice_date')
        batch_op.drop_column('dues23_invoice')
        batch_op.drop_column('dues23_balanced')
        batch_op.drop_column('dues23_balance')
        batch_op.drop_column('dues23_amount_reduced')
        batch_op.drop_column('dues23_amount_paid')
        batch_op.drop_column('dues23_amount')

    op.drop_table('dues23invoices')
