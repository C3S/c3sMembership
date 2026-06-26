# -*- coding: utf-8  -*-
"""
Dues invoice

A single table holding the dues invoices of all years. The year of the invoice
is stored in the ``year`` column. This replaces the former per-year invoice
tables (``dues15invoices`` ... ``dues26invoices``).

Invoice numbers restart at 1 for each year. Therefore uniqueness of the invoice
number and the invoice number string is enforced per year via composite unique
constraints rather than globally.
"""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Unicode,
    UniqueConstraint,
)

from c3smembership.data.model.base import (
    Base,
    DatabaseDecimal,
)


class DuesInvoice(Base):
    """
    This table stores the dues invoices of all years.

    We need this for bookkeeping, because whenever a member is granted a
    reduction of her dues, the old invoice is canceled by a reversal invoice and
    a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.
    """
    __tablename__ = 'dues_invoices'
    __table_args__ = (
        UniqueConstraint('year', 'invoice_no', name='uq_dues_invoices_year_no'),
        UniqueConstraint(
            'year', 'invoice_no_string',
            name='uq_dues_invoices_year_no_string'),
    )
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    year = Column(Integer())
    """the dues year the invoice belongs to, e.g. 2026"""
    # this invoice
    invoice_no = Column(Integer())
    """invoice number, unique within the year"""
    invoice_no_string = Column(Unicode(255))
    """invoice number string, unique within the year"""
    invoice_date = Column(DateTime())
    """timestamp of invoice creation (DateTime)"""
    invoice_amount = Column(DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """amount (DatabaseDecimal(12,2))"""
    # has it been superseeded by reversal?
    is_cancelled = Column(Boolean, default=False)
    """flag: invoice has been superseeded by reversal or cancellation"""
    cancelled_date = Column(DateTime())
    """timestamp of cancellation/reversal"""
    # is it a reversal?
    is_reversal = Column(Boolean, default=False)
    """flag: is this a reversal invoice?"""
    # is it a reduction (or even more than default)?
    is_altered = Column(Boolean, default=False)
    """flag: has the amount been reduced or increased?"""
    # person reference
    member_id = Column(Integer())
    """reference to C3sMember id"""
    membership_no = Column(Integer())
    """reference to C3sMember membership_number"""
    email = Column(Unicode(255))
    """C3sMembers email we sent this invoice to"""
    token = Column(Unicode(255))
    """used to limit access to this invoice"""
    # referrals
    preceding_invoice_no = Column(Integer(), default=None)
    """the invoice number preceeding this one, if applicable"""
    succeeding_invoice_no = Column(Integer(), default=None)
    """the invoice number succeeding this one, if applicable"""

    def __init__(
            self,
            year,
            invoice_no,
            invoice_no_string,
            invoice_date,
            invoice_amount,
            member_id,
            membership_no,
            email,
            token):
        """
        Make a new invoice object

        Args:
            year: the dues year the invoice belongs to
            invoice_no: invoice number
            invoice_no_string: invoice number string
            invoice_date: timestamp of creation
            invoice_amount: amount of money
            member_id: references C3sMember
            membership_no: references C3sMember
            email: email to send it to
            token: a token to limit access
        """
        self.year = year
        self.invoice_no = invoice_no
        self.invoice_no_string = invoice_no_string
        self.invoice_date = invoice_date
        self.invoice_amount = invoice_amount
        self.member_id = member_id
        self.membership_no = membership_no
        self.email = email
        self.token = token
