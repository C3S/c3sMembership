# -*- coding: utf-8  -*-
"""
Dues 2015 invoice
"""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Unicode,
)

from c3smembership.data.model.base import (
    Base,
    DatabaseDecimal,
)


class Dues15Invoice(Base):
    """
    This table stores the invoices for the 2015 version of dues.

    We need this for bookkeeping,
    because whenever a member is granted a reduction of her dues,
    the old invoice is canceled by a reversal invoice
    and a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.

    """
    __tablename__ = 'dues15invoices'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    # this invoice
    invoice_no = Column(Integer(), unique=True)
    """invoice number (Integer, unique)"""
    invoice_no_string = Column(Unicode(255), unique=True)
    """invoice number string (unique)"""
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
            invoice_no: invoice number
            invoice_no_string: invoice number string
            invoice_date: timestamp of creation
            invoice_amount: amount of money
            member_id: references C3sMember
            membership_no: references C3sMember
            email: email to send it to
            token: a token to limit access
        """
        self.invoice_no = invoice_no
        self.invoice_no_string = invoice_no_string
        self.invoice_date = invoice_date
        self.invoice_amount = invoice_amount
        self.member_id = member_id
        self.membership_no = membership_no
        self.email = email
        self.token = token
