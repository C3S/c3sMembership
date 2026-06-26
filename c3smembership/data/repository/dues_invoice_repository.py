# -*- coding: utf-8  -*-
"""
Repository for operating with dues invoices

The dues invoices of all years are stored in a single ``dues_invoices`` table
(see :class:`c3smembership.data.model.base.dues_invoice.DuesInvoice`) and the
per-member, per-year dues accounts in a single ``dues`` table (see
:class:`c3smembership.data.model.base.dues.Dues`). The year is a regular data
column, so supporting a new year does not require any data model or code change.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.sql import (
    expression,
    func,
)

from c3smembership.data.model.base import (
    DBSession,
    DatabaseDecimal,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues import Dues
from c3smembership.data.model.base.dues_invoice import DuesInvoice


class DuesInvoiceRepository(object):
    """
    Repository for operating with dues invoices
    """

    @classmethod
    def get_all(cls, years=None):
        """
        Get dues invoices

        If years is not specified then all available years are returned.

        Args:
            years (array): Defaults to None. An array of ints representing
                years, e.g. 2019.

        Returns:
            An array of dues invoices for the years specified.

        Example:
            dues_invoices = DuesInvoiceRepository.get_all([2015, 2018])
        """
        db_session = DBSession()
        query = db_session.query(DuesInvoice)
        if years is not None:
            query = query.filter(DuesInvoice.year.in_(years))
        return query.order_by(DuesInvoice.year, DuesInvoice.id).all()

    @classmethod
    def get_by_number(cls, invoice_number, year):
        """
        Get the dues invoice by invoice number

        Args:
            invoice_number (int): The invoice number for the invoice to be
                retrieved
            year (int): The year to which the invoice number belongs, e.g.
                2019.

        Returns:
            The invoice having the invoice number for the specified year.
        """
        db_session = DBSession()
        return db_session \
            .query(DuesInvoice) \
            .filter(DuesInvoice.year == year) \
            .filter(DuesInvoice.invoice_no == invoice_number) \
            .first()

    @classmethod
    def get_by_membership_number(cls, membership_number, years=None):
        """
        Get dues invoices of a member by their membership number

        Args:
            membership_number (int): The membership number of the member for
                which the invoices are retrieved.
            years (array): Defaults to None. An array of ints representing
                years, e.g. 2019.

        Returns:
            An array of invoices of the member for the year specified.
        """
        db_session = DBSession()
        query = db_session \
            .query(DuesInvoice) \
            .join(C3sMember, C3sMember.id == DuesInvoice.member_id) \
            .filter(C3sMember.membership_number == membership_number)
        if years is not None:
            query = query.filter(DuesInvoice.year.in_(years))
        return query.order_by(DuesInvoice.year, DuesInvoice.id).all()

    @classmethod
    def get_max_invoice_number(cls, year):
        """
        Get the maximum invoice number for a specific year

        If no invoice number has been assigned yet, the method returns 0.

        Args:
            year (int): The year to which the invoice number belongs, e.g.
                2019.

        Returns:
            An int representing the maximum invoice numbers, 0 if no invoice
            number has been assigned yet.
        """
        result = 0
        db_session = DBSession()
        max_invoice_number, = db_session \
            .query(func.max(DuesInvoice.invoice_no)) \
            .filter(DuesInvoice.year == year) \
            .first()
        if max_invoice_number is not None:
            result = max_invoice_number
        return result

    @classmethod
    def create_dues_invoice(cls, year, member, invoice_number,
                            invoice_number_string, invoice_amount,
                            invoice_token):
        """
        Create dues invoice

        Args:
            year (int): The year for which the invoice is created.
            member (C3sMember): The member for which the invoice is created.
            invoice_number (int): The number of the invoice which identifies it
                uniquely within the year.
            invoice_number_string (str): The string representation of the
                invoice number.
            invoice_amount (Decimal): The amount of the invoice.
            invoice_token (str): Token to uniquely identify the invoice. The
                token can be used as a secret to invoices from being accessed
                without permission.
        """
        invoice = DuesInvoice(
            year=year,
            invoice_no=invoice_number,
            invoice_no_string=invoice_number_string,
            invoice_date=datetime.now(),
            invoice_amount='' + str(invoice_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=invoice_token,
        )
        DBSession().add(invoice)

        dues = member.get_dues(year)
        dues.invoice_no = invoice_number
        dues.token = invoice_token
        DBSession().flush()

        return invoice

    @classmethod
    def store_dues(cls, year, member, dues_calculation):
        """
        Store the calculated dues amount on the member's dues account.
        """
        dues = member.get_dues(year)
        dues.set_amount(dues_calculation.amount)
        dues.start = dues_calculation.code
        DBSession().flush()

    @classmethod
    def record_dues_email_sent(cls, year, member):
        """
        Record the fact that the dues email was sent and when it was sent
        """
        dues = member.get_dues(year)
        dues.invoice = True
        dues.invoice_date = datetime.now()
        DBSession().flush()

    @classmethod
    def token_exists(cls, token, year):
        """
        Indicates whether a token exists for a specific year

        Args:
            token (str): A token string.
            year (int): The year in which to check for the token.

        Returns:
            Boolean indicating whether the token exists for the year.
        """
        db_session = DBSession()
        invoice = db_session \
            .query(DuesInvoice) \
            .filter(DuesInvoice.year == year) \
            .filter(DuesInvoice.token == token) \
            .first()
        return invoice is not None

    @classmethod
    def get_monthly_stats(cls, year):
        """
        Gets monthly statistics for the specified year

        Args:
            year (int): The year to which the invoice number belongs, e.g.
                2019.

        Returns:
            Sums of the normal and reversal invoices per calendar month based
            on the invoice date.
        """
        db_session = DBSession()
        result = []

        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        invoice_date_month = func.substr(DuesInvoice.invoice_date, 1, 7)
        payment_date_month = func.substr(Dues.paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = db_session.query(
            invoice_date_month.label('month'),
            func.sum(
                expression.case(
                    (expression.not_(
                        DuesInvoice.is_reversal), DuesInvoice.invoice_amount),
                    else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(
                expression.case(
                    (DuesInvoice.is_reversal, DuesInvoice.invoice_amount),
                    else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column('\'0.0\'', DatabaseDecimal).label(
                'amount_paid')) \
            .filter(DuesInvoice.year == year) \
            .group_by(invoice_date_month)

        # collect the payments per month
        member_payments_query = db_session.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(Dues.amount_paid).label('amount_paid')
        ).filter(Dues.year == year) \
            .filter(Dues.paid_date.isnot(None)) \
            .group_by(payment_date_month)

        # union invoice amounts and payments
        union_all_query = expression.union_all(
            member_payments_query, invoice_amounts_query).subquery()

        # aggregate invoice amounts and payments by month
        result_query = db_session.query(
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
            result.append({
                'month': datetime(int(month_stat[0][0:4]),
                                  int(month_stat[0][5:7]), 1),
                'amount_invoiced_normal': month_stat[1],
                'amount_invoiced_reversal': month_stat[2],
                'amount_paid': month_stat[3]
            })
        return result
