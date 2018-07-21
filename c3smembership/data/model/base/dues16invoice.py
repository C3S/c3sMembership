# -*- coding: utf-8  -*-
"""
Dues 2016 invoice
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Unicode,
)
from sqlalchemy.sql import func
from sqlalchemy.sql import expression

from c3smembership.data.model.base import (
    Base,
    DatabaseDecimal,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember


class Dues16Invoice(Base):
    """
    This table stores the invoices for the 2015 version of dues.

    We need this for bookkeeping,
    because whenever a member is granted a reduction of her dues,
    the old invoice is canceled by a reversal invoice
    and a new invoice must be issued.

    Edge case: if reduced to 0, no new invoice needed.

    """
    __tablename__ = 'dues16invoices'
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

    @classmethod
    def get_all(cls):
        """
        Return all dues16 invoices
        """
        return DBSession.query(cls).all()

    @classmethod
    def get_by_invoice_no(cls, _no):
        """return one invoice by invoice number"""
        return DBSession.query(cls).filter(cls.invoice_no == _no).first()

    @classmethod
    def get_by_membership_no(cls, _no):
        """return all invoices of one member by membership number"""
        return DBSession.query(cls).filter(cls.membership_no == _no).all()

    @classmethod
    def get_max_invoice_no(cls):
        """
        Get the maximum invoice number.

        Returns:
            * Integer: maximum of given invoice numbers or 0"""
        res, = DBSession.query(func.max(cls.id)).first()

        if res is None:
            return 0
        return res

    @classmethod
    def check_for_existing_dues16_token(cls, dues_token):
        """
        Check if a dues token is already present.

        Args:
            dues_token: a given string

        Returns:
            * **True**, if token already in table
            * **False** else
        """
        check = DBSession.query(cls).filter(
            cls.token == dues_token).first()
        return check is not None

    @classmethod
    def get_monthly_stats(cls):
        """
        Gets the monthly statistics.

        Provides sums of the normale as well as reversal invoices per
        calendar month based on the invoice date.
        """
        result = []
        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        # invoice_date_month = func.date_trunc(
        #     'month',
        #     Dues16Invoice.invoice_date)
        invoice_date_month = func.substr(Dues16Invoice.invoice_date, 1, 7)
        payment_date_month = func.substr(C3sMember.dues16_paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = DBSession.query(
            invoice_date_month.label('month'),
            func.sum(expression.case(
                [(
                    expression.not_(Dues16Invoice.is_reversal),
                    Dues16Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(expression.case(
                [(
                    Dues16Invoice.is_reversal,
                    Dues16Invoice.invoice_amount)],
                else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal).label('amount_paid')
        ).group_by(invoice_date_month)
        # collect the payments per month
        member_payments_query = DBSession.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(C3sMember.dues16_amount_paid).label('amount_paid')
        ).filter(C3sMember.dues16_paid_date.isnot(None)) \
            .group_by(payment_date_month)
        # union invoice amounts and payments
        union_all_query = expression.union_all(
            member_payments_query, invoice_amounts_query)
        # aggregate invoice amounts and payments by month
        result_query = DBSession.query(
            union_all_query.c.month.label('month'),
            func.sum(union_all_query.c.amount_invoiced_normal).label(
                'amount_invoiced_normal'),
            func.sum(union_all_query.c.amount_invoiced_reversal).label(
                'amount_invoiced_reversal'),
            func.sum(union_all_query.c.amount_paid).label('amount_paid')
        ) \
            .group_by(union_all_query.c.month) \
            .order_by(union_all_query.c.month)
        for month_stat in result_query.all():
            result.append(
                {
                    'month': datetime(
                        int(month_stat[0][0:4]),
                        int(month_stat[0][5:7]),
                        1),
                    'amount_invoiced_normal': month_stat[1],
                    'amount_invoiced_reversal': month_stat[2],
                    'amount_paid': month_stat[3]
                })
        return result
