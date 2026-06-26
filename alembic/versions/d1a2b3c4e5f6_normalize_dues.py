"""Normalize dues data model

Replace the per-year dues design (one set of ``duesNN_*`` columns on the
``members`` table plus one ``duesNNinvoices`` table per year) with two normalized
tables:

* ``dues_invoices`` -- all dues invoices of all years, with a ``year`` column.
* ``dues`` -- the per-member, per-year dues account, with a ``year`` column.

The existing data is migrated into the new tables and the old columns and tables
are dropped in this same migration.

Revision ID: d1a2b3c4e5f6
Revises: c5d3e9a8f2b1
Create Date: 2026-06-26 00:00:00.000000

"""

from decimal import Decimal

from alembic import op
import sqlalchemy as sa
import sqlalchemy.types as types
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'd1a2b3c4e5f6'
down_revision = 'c5d3e9a8f2b1'


YEARS = list(range(2015, 2027))


class SqliteDecimal(types.TypeDecorator):
    """
    Type decorator for persisting Decimal (currency values)
    """
    impl = types.String
    cache_ok = False

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return None

    def process_result_value(self, value, dialect):
        if value is not None and value != '':
            return Decimal(value)
        return None


# The 13 per-year dues columns on the members table, as (suffix, column factory).
def _member_dues_columns(short):
    """
    Build the list of per-year dues columns for a two-digit year suffix.
    """
    return [
        sa.Column('dues{0}_invoice'.format(short), sa.Boolean(),
                  nullable=True, default=False),
        sa.Column('dues{0}_invoice_date'.format(short), sa.DateTime(),
                  nullable=True),
        sa.Column('dues{0}_invoice_no'.format(short), sa.Integer(),
                  nullable=True),
        sa.Column('dues{0}_token'.format(short), sa.Unicode(length=10),
                  nullable=True),
        sa.Column('dues{0}_start'.format(short), sa.Unicode(length=255),
                  nullable=True),
        sa.Column('dues{0}_amount'.format(short),
                  SqliteDecimal(length=12, collation=2), nullable=True),
        sa.Column('dues{0}_reduced'.format(short), sa.Boolean(),
                  nullable=True, default=False),
        sa.Column('dues{0}_amount_reduced'.format(short),
                  SqliteDecimal(length=12, collation=2), nullable=True),
        sa.Column('dues{0}_balance'.format(short),
                  SqliteDecimal(length=12, collation=2), nullable=True),
        sa.Column('dues{0}_balanced'.format(short), sa.Boolean(),
                  nullable=True, default=True),
        sa.Column('dues{0}_paid'.format(short), sa.Boolean(),
                  nullable=True, default=False),
        sa.Column('dues{0}_amount_paid'.format(short),
                  SqliteDecimal(length=12, collation=2), nullable=True),
        sa.Column('dues{0}_paid_date'.format(short), sa.DateTime(),
                  nullable=True),
    ]


def _create_dues_invoice_table(name):
    """
    Create a per-year invoice table (used in downgrade only).
    """
    op.create_table(
        name,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_no', sa.Integer(), nullable=True),
        sa.Column('invoice_no_string', sa.Unicode(length=255), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('invoice_amount', SqliteDecimal(length=12, collation=2),
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
        sa.UniqueConstraint('invoice_no_string'))


# invoice columns shared by the old per-year tables and the new combined table
_INVOICE_COLUMNS = [
    'invoice_no', 'invoice_no_string', 'invoice_date', 'invoice_amount',
    'is_cancelled', 'cancelled_date', 'is_reversal', 'is_altered',
    'member_id', 'membership_no', 'email', 'token',
    'preceding_invoice_no', 'succeeding_invoice_no',
]


def upgrade():
    bind = op.get_bind()

    # 1. Create the new normalized tables.
    op.create_table(
        'dues_invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('invoice_no', sa.Integer(), nullable=True),
        sa.Column('invoice_no_string', sa.Unicode(length=255), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('invoice_amount', SqliteDecimal(length=12, collation=2),
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
        sa.UniqueConstraint('year', 'invoice_no',
                            name='uq_dues_invoices_year_no'),
        sa.UniqueConstraint('year', 'invoice_no_string',
                            name='uq_dues_invoices_year_no_string'))

    op.create_table(
        'dues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('invoice', sa.Boolean(), nullable=True),
        sa.Column('invoice_date', sa.DateTime(), nullable=True),
        sa.Column('invoice_no', sa.Integer(), nullable=True),
        sa.Column('token', sa.Unicode(length=10), nullable=True),
        sa.Column('start', sa.Unicode(length=255), nullable=True),
        sa.Column('amount', SqliteDecimal(length=12, collation=2),
                  nullable=True),
        sa.Column('reduced', sa.Boolean(), nullable=True),
        sa.Column('amount_reduced', SqliteDecimal(length=12, collation=2),
                  nullable=True),
        sa.Column('balance', SqliteDecimal(length=12, collation=2),
                  nullable=True),
        sa.Column('balanced', sa.Boolean(), nullable=True),
        sa.Column('paid', sa.Boolean(), nullable=True),
        sa.Column('amount_paid', SqliteDecimal(length=12, collation=2),
                  nullable=True),
        sa.Column('paid_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('member_id', 'year', name='uq_dues_member_year'))

    # 2. Backfill the invoices from each per-year invoice table.
    invoice_cols = ', '.join(_INVOICE_COLUMNS)
    for year in YEARS:
        short = year % 100
        bind.execute(text(
            'INSERT INTO dues_invoices (year, {cols}) '
            'SELECT {year}, {cols} FROM dues{short:02d}invoices'.format(
                cols=invoice_cols, year=year, short=short)))

    # 3. Backfill the dues accounts from the members columns, one row per
    #    member and year which actually has dues activity.
    for year in YEARS:
        short = '{0:02d}'.format(year % 100)
        bind.execute(text(
            'INSERT INTO dues ('
            '  member_id, year, invoice, invoice_date, invoice_no, token,'
            '  start, amount, reduced, amount_reduced, balance, balanced,'
            '  paid, amount_paid, paid_date) '
            'SELECT id, :year, '
            '  dues{s}_invoice, dues{s}_invoice_date, dues{s}_invoice_no,'
            '  dues{s}_token, dues{s}_start, dues{s}_amount, dues{s}_reduced,'
            '  dues{s}_amount_reduced, dues{s}_balance, dues{s}_balanced,'
            '  dues{s}_paid, dues{s}_amount_paid, dues{s}_paid_date '
            'FROM members '
            'WHERE dues{s}_invoice = 1 '
            '   OR dues{s}_paid = 1 '
            '   OR dues{s}_invoice_no IS NOT NULL '
            "   OR (dues{s}_amount IS NOT NULL AND dues{s}_amount "
            "       NOT IN ('NaN', '') AND CAST(dues{s}_amount AS REAL) != 0) "
            '   OR (dues{s}_amount_paid IS NOT NULL '
            '       AND CAST(dues{s}_amount_paid AS REAL) != 0) '
            '   OR (dues{s}_balance IS NOT NULL '
            '       AND CAST(dues{s}_balance AS REAL) != 0)'.format(s=short)
        ), {'year': year})

    # 4. Drop the per-year invoice tables.
    for year in YEARS:
        op.drop_table('dues{0:02d}invoices'.format(year % 100))

    # 5. Drop the per-year columns from the members table.
    with op.batch_alter_table('members', schema=None) as batch_op:
        for year in YEARS:
            short = '{0:02d}'.format(year % 100)
            for column in _member_dues_columns(short):
                batch_op.drop_column(column.name)


def downgrade():
    # Note: this recreates the previous structure but does NOT restore the
    # migrated data. The data now lives in the ``dues`` and ``dues_invoices``
    # tables which are dropped here.
    with op.batch_alter_table('members', schema=None) as batch_op:
        for year in YEARS:
            short = '{0:02d}'.format(year % 100)
            for column in _member_dues_columns(short):
                batch_op.add_column(column)

    for year in YEARS:
        _create_dues_invoice_table('dues{0:02d}invoices'.format(year % 100))

    op.drop_table('dues')
    op.drop_table('dues_invoices')
