"""Dues 2018

Revision ID: 4a12432fa915
Revises: d4c59e012aa
Create Date: 2018-06-18 15:54:13.943481

"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types


# revision identifiers, used by Alembic.
revision = '4a12432fa915'
down_revision = 'd4c59e012aa'


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
        'dues18invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_no', sa.Integer(), nullable=True),
        sa.Column('invoice_no_string', sa.Unicode(length=255), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column(
            'invoice_amount',
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_no'),
        sa.UniqueConstraint('invoice_no_string')
    )
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'dues18_amount',
            SqliteDecimal(length=12, collation=2),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_amount_paid',
            SqliteDecimal(length=12, collation=2),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_amount_reduced',
            SqliteDecimal(length=12, collation=2),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_balance',
            SqliteDecimal(length=12, collation=2),
            nullable=True,
            default=Decimal('0.0')))
        batch_op.add_column(sa.Column(
            'dues18_balanced',
            sa.Boolean(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_invoice',
            sa.Boolean(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_invoice_date',
            sa.DateTime(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_invoice_no',
            sa.Integer(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_paid',
            sa.Boolean(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_paid_date',
            sa.DateTime(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_reduced',
            sa.Boolean(),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_start',
            sa.Unicode(length=255),
            nullable=True))
        batch_op.add_column(sa.Column(
            'dues18_token',
            sa.Unicode(length=10),
            nullable=True))


def downgrade():
    with op.batch_alter_table(u'members', schema=None) as batch_op:
        batch_op.drop_column('dues18_token')
        batch_op.drop_column('dues18_start')
        batch_op.drop_column('dues18_reduced')
        batch_op.drop_column('dues18_paid_date')
        batch_op.drop_column('dues18_paid')
        batch_op.drop_column('dues18_invoice_no')
        batch_op.drop_column('dues18_invoice_date')
        batch_op.drop_column('dues18_invoice')
        batch_op.drop_column('dues18_balanced')
        batch_op.drop_column('dues18_balance')
        batch_op.drop_column('dues18_amount_reduced')
        batch_op.drop_column('dues18_amount_paid')
        batch_op.drop_column('dues18_amount')

    op.drop_table('dues18invoices')
