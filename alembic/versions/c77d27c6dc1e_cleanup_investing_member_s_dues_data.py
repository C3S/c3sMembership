"""Cleanup investing member's dues data

Revision ID: c77d27c6dc1e
Revises: 80b504eeda8a
Create Date: 2020-03-04 20:28:54.918197

"""
from decimal import Decimal

from alembic import op
from sqlalchemy import update
from sqlalchemy.orm import Session

from c3smembership.data.model.base.c3smember import C3sMember

# revision identifiers, used by Alembic.
revision = 'c77d27c6dc1e'
down_revision = '80b504eeda8a'


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues15_amount=Decimal('NaN'),
                dues15_invoice_no=None,
                dues15_token=None,
                dues15_start=None,
                dues15_reduced=False,
                dues15_amount_reduced=Decimal('NaN'),
                dues15_balance=Decimal('0'),
                dues15_balanced=False,
                dues15_paid=False,
                dues15_amount_paid=Decimal('0'),
                dues15_paid_date=None))
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues16_amount=Decimal('NaN'),
                dues16_invoice_no=None,
                dues16_token=None,
                dues16_start=None,
                dues16_reduced=False,
                dues16_amount_reduced=Decimal('NaN'),
                dues16_balance=Decimal('0'),
                dues16_balanced=False,
                dues16_paid=False,
                dues16_amount_paid=Decimal('0'),
                dues16_paid_date=None))
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues17_amount=Decimal('NaN'),
                dues17_invoice_no=None,
                dues17_token=None,
                dues17_start=None,
                dues17_reduced=False,
                dues17_amount_reduced=Decimal('NaN'),
                dues17_balance=Decimal('0'),
                dues17_balanced=False,
                dues17_paid=False,
                dues17_amount_paid=Decimal('0'),
                dues17_paid_date=None))
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues18_amount=Decimal('NaN'),
                dues18_invoice_no=None,
                dues18_token=None,
                dues18_start=None,
                dues18_reduced=False,
                dues18_amount_reduced=Decimal('NaN'),
                dues18_balance=Decimal('0'),
                dues18_balanced=False,
                dues18_paid=False,
                dues18_amount_paid=Decimal('0'),
                dues18_paid_date=None))
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues19_amount=Decimal('NaN'),
                dues19_invoice_no=None,
                dues19_token=None,
                dues19_start=None,
                dues19_reduced=False,
                dues19_amount_reduced=Decimal('NaN'),
                dues19_balance=Decimal('0'),
                dues19_balanced=False,
                dues19_paid=False,
                dues19_amount_paid=Decimal('0'),
                dues19_paid_date=None))
    session.execute(
        update(C3sMember).where(
            C3sMember.membership_type == u'investing').values(
                dues20_amount=Decimal('NaN'),
                dues20_invoice_no=None,
                dues20_token=None,
                dues20_start=None,
                dues20_reduced=False,
                dues20_amount_reduced=Decimal('NaN'),
                dues20_balance=Decimal('0'),
                dues20_balanced=False,
                dues20_paid=False,
                dues20_amount_paid=Decimal('0'),
                dues20_paid_date=None))
    session.flush()
    session.commit()


def downgrade():
    pass
