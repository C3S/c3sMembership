# -*- coding: utf-8  -*-
"""
Dues account

A single table holding the per-member, per-year dues account. This replaces the
former ~130 ``duesXX_*`` columns on the ``members`` table. There is at most one
row per member and year, enforced by a composite unique constraint.
"""

from decimal import Decimal
import math

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.ext.hybrid import hybrid_property

from c3smembership.data.model.base import (
    Base,
    DatabaseDecimal,
)


class Dues(Base):
    """
    The dues account of a member for a specific year.

    Stores the calculated and reduced dues amount, the balance, the payment
    information and the invoice reference for one member and one year.
    """
    __tablename__ = 'dues'
    __table_args__ = (
        UniqueConstraint('member_id', 'year', name='uq_dues_member_year'),
    )
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """tech. id. / no. in table (integer, primary key)"""
    member_id = Column(Integer, ForeignKey('members.id'))
    """reference to the C3sMember the dues account belongs to"""
    year = Column(Integer())
    """the dues year the account belongs to, e.g. 2026"""

    # invoice
    invoice = Column(Boolean, default=False)
    """flag: has the dues invoice email been sent?"""
    invoice_date = Column(DateTime())
    """timestamp of the dues invoice email"""
    invoice_no = Column(Integer())
    """the currently active invoice number for the member and year"""
    token = Column(Unicode(10))
    """access token for the invoice"""
    start = Column(Unicode(255))
    """quarter of membership within the dues year"""

    # amount
    amount = Column(DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """calculated amount the member has to pay by default"""
    reduced = Column(Boolean, default=False)
    """flag: has the amount been reduced?"""
    _amount_reduced = Column(
        'amount_reduced',
        DatabaseDecimal(12, 2), default=Decimal('NaN'))
    """the amount the dues were reduced to"""

    # balance
    _balance = Column(
        'balance',
        DatabaseDecimal(12, 2), default=Decimal('0'))
    """the amount still to be settled"""
    balanced = Column(Boolean, default=True)
    """flag: is the balance settled?"""

    # payment
    paid = Column(Boolean, default=False)
    """flag: has a payment been received?"""
    amount_paid = Column(DatabaseDecimal(12, 2), default=Decimal('0'))
    """how much has been paid?"""
    paid_date = Column(DateTime())
    """timestamp of the payment"""

    def __init__(self, member_id, year):
        """
        Create a new dues account for a member and year.

        The defaults mirror the column defaults so that an account which has not
        been persisted yet can be read with sensible values.
        """
        self.member_id = member_id
        self.year = year
        self.invoice = False
        self.amount = Decimal('NaN')
        self.reduced = False
        self._amount_reduced = Decimal('NaN')
        self._balance = Decimal('0')
        self.balanced = True
        self.paid = False
        self.amount_paid = Decimal('0')

    @hybrid_property
    def balance(self):
        """
        Get the dues balance, i.e. amount due subtracted by amount paid.
        """
        return self._balance

    @balance.setter
    def balance(self, balance):
        """
        Set the dues balance.

        If balance is set to 0 the balanced flag is set to True.
        """
        self._balance = balance
        self.balanced = self._balance == Decimal('0')

    @hybrid_property
    def amount_reduced(self):
        """
        Get the reduced dues amount.

        The originally calculated dues amount can be reduced on member's
        request. This gets the amount the dues were reduced to.
        """
        return self._amount_reduced

    @amount_reduced.setter
    def amount_reduced(self, amount_reduced):
        """
        Set the reduced dues amount.

        The originally calculated dues amount can be reduced on member's
        request. This sets the amount the dues were reduced to.
        """
        self._amount_reduced = amount_reduced
        self.reduced = (
            not math.isnan(self.amount_reduced)
            and
            self.amount_reduced != self.amount)

    def set_payment(self, paid_amount, paid_date):
        """
        Record a payment, accumulating the paid amount and reducing the balance.
        """
        if self.amount_paid is None or math.isnan(self.amount_paid):
            amount_paid = Decimal('0')
        else:
            amount_paid = self.amount_paid

        self.paid = True
        self.amount_paid = amount_paid + paid_amount
        self.paid_date = paid_date
        self.balance = self.balance - paid_amount

    def set_amount(self, dues_amount):
        """
        Set the calculated dues amount and update the balance accordingly.
        """
        if self.amount is None or math.isnan(self.amount) \
                or not isinstance(self.amount, Decimal):
            amount = Decimal('0')
        else:
            amount = self.amount

        self.balance = self.balance - amount + Decimal(dues_amount)
        self.amount = dues_amount

    def set_reduced_amount(self, reduced_amount):
        """
        Set the reduced dues amount and update the balance accordingly.
        """
        if reduced_amount != self.amount:
            previous_amount_in_balance = (
                self.amount_reduced
                if self.reduced
                else self.amount)
            self.balance = self.balance - \
                previous_amount_in_balance + reduced_amount
            self.amount_reduced = reduced_amount
        else:
            self.amount_reduced = Decimal('NaN')
