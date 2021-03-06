# -*- coding: utf-8  -*-
"""
Repository for operating with dues invoices

The DuesInvoiceRepository is still being built up. It needs to abstract the
database structures from the business and presentation layers. Once this
abstraction is finalized the dues invoices data model can be changed to contain
all years in one table in order to not have to alter the data model for
following years.
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
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice
from c3smembership.data.model.base.dues19invoice import Dues19Invoice
from c3smembership.data.model.base.dues20invoice import Dues20Invoice
from c3smembership.data.model.base.dues21invoice import Dues21Invoice


class DuesInvoiceRepository(object):
    """
    Repository for operating with dues invoices

    The constants _DUES_INVOICE_CLASS and _PAYMENT_FIELDS are workarounds until
    the data model is cleaned up, agnostic to the year and does not contain any
    payment information on the member record.
    """
    # pylint: disable=too-few-public-methods

    _DUES_INVOICE_CLASS = {
        2015: Dues15Invoice,
        2016: Dues16Invoice,
        2017: Dues17Invoice,
        2018: Dues18Invoice,
        2019: Dues19Invoice,
        2020: Dues20Invoice,
        2021: Dues21Invoice,
    }
    _PAYMENT_FIELDS = {
        2015: {
            'paid_date': C3sMember.dues15_paid_date,
            'amount_paid': C3sMember.dues15_amount_paid,
        },
        2016: {
            'paid_date': C3sMember.dues16_paid_date,
            'amount_paid': C3sMember.dues16_amount_paid,
        },
        2017: {
            'paid_date': C3sMember.dues17_paid_date,
            'amount_paid': C3sMember.dues17_amount_paid,
        },
        2018: {
            'paid_date': C3sMember.dues18_paid_date,
            'amount_paid': C3sMember.dues18_amount_paid,
        },
        2019: {
            'paid_date': C3sMember.dues19_paid_date,
            'amount_paid': C3sMember.dues19_amount_paid,
        },
        2020: {
            'paid_date': C3sMember.dues20_paid_date,
            'amount_paid': C3sMember.dues20_amount_paid,
        },
        2021: {
            'paid_date': C3sMember.dues21_paid_date,
            'amount_paid': C3sMember.dues21_amount_paid,
        },
    }

    @classmethod
    def _get_year_classes(cls, years=None):
        """
        Get the dues data model classes for the years

        If years is not specified then all available years are returned.

        Args:
            years (array): Defaults to None. An array of ints representing
                years, e.g. 2019.

        Returns:
            An array of dues data model classes.
        """
        year_classes = []

        # Fill all years if None
        if years is None:
            years = []
            for year in cls._DUES_INVOICE_CLASS:
                years.append(year)

        # Get years classes
        for year in years:
            if year in cls._DUES_INVOICE_CLASS:
                year_classes.append(cls._DUES_INVOICE_CLASS[year])
        return year_classes

    @classmethod
    def _get_year_class(cls, year):
        """
        Get the dues data model class for the year

        Args:
            year (int): The year to which the invoice number belongs, e.g.
                2019.

        Returns:
            The dues data model class for the year.
        """
        result = None
        year_classes = cls._get_year_classes([year])
        if len(year_classes) > 0:
            result = year_classes[0]
        return result

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
        result = []
        db_session = DBSession()
        year_classes = cls._get_year_classes(years)
        for year_class in year_classes:
            result = result + db_session.query(year_class).all()
        return result

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
        result = None
        db_session = DBSession()
        year_class = cls._get_year_class(year)
        if year_class is not None:
            result = db_session \
                .query(year_class) \
                .filter(year_class.invoice_no == invoice_number) \
                .first()
        return result

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
        result = []
        db_session = DBSession()
        year_classes = cls._get_year_classes(years)
        for year_class in year_classes:
            result = result + db_session \
                .query(year_class) \
                .join(
                    C3sMember,
                    C3sMember.id == year_class.member_id) \
                .filter(C3sMember.membership_number == membership_number) \
                .all()
        return result

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
        year_class = cls._get_year_class(year)
        if year_class is not None:
            max_invoice_number, = db_session \
                .query(func.max(year_class.invoice_no)) \
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
        dues_invoice_class = cls._get_dues_invoice_class(year)
        invoice = dues_invoice_class(
            invoice_no=invoice_number,
            invoice_no_string=invoice_number_string,
            invoice_date=datetime.now(),
            invoice_amount=u'' + str(invoice_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=invoice_token,
        )
        DBSession().add(invoice)

        if year == 2015:
            member.dues15_invoice_no = invoice_number
            member.dues15_token = invoice_token
        if year == 2016:
            member.dues16_invoice_no = invoice_number
            member.dues16_token = invoice_token
        if year == 2017:
            member.dues17_invoice_no = invoice_number
            member.dues17_token = invoice_token
        if year == 2018:
            member.dues18_invoice_no = invoice_number
            member.dues18_token = invoice_token
        if year == 2019:
            member.dues19_invoice_no = invoice_number
            member.dues19_token = invoice_token
        if year == 2020:
            member.dues20_invoice_no = invoice_number
            member.dues20_token = invoice_token
        if year == 2021:
            member.dues21_invoice_no = invoice_number
            member.dues21_token = invoice_token
        DBSession().flush()

        return invoice

    @classmethod
    def store_dues(cls, year, member, dues_calculation):
        """
        Store the dues

        TODO: This is only a workaround until the data model has been cleaned
        up and there is an extra table to record dues per year and member.
        """
        if year == 2015:
            member.set_dues15_amount(dues_calculation.amount)
            member.dues15_start = dues_calculation.code
        if year == 2016:
            member.set_dues16_amount(dues_calculation.amount)
            member.dues16_start = dues_calculation.code
        if year == 2017:
            member.set_dues17_amount(dues_calculation.amount)
            member.dues17_start = dues_calculation.code
        if year == 2018:
            member.set_dues18_amount(dues_calculation.amount)
            member.dues18_start = dues_calculation.code
        if year == 2019:
            member.set_dues19_amount(dues_calculation.amount)
            member.dues19_start = dues_calculation.code
        if year == 2020:
            member.set_dues20_amount(dues_calculation.amount)
            member.dues20_start = dues_calculation.code
        if year == 2021:
            member.set_dues21_amount(dues_calculation.amount)
            member.dues21_start = dues_calculation.code
        DBSession().flush()

    @classmethod
    def record_dues_email_sent(cls, year, member):
        """
        Record the fact that the dues email was sent and when it was sent
        """
        # TODO: This is only a workaround until the data model has been cleaned
        # up and there is an extra table to record dues per year and member.
        invoice_date = datetime.now()
        if year == 2015:
            member.dues15_invoice = True
            member.dues15_invoice_date = invoice_date
        if year == 2016:
            member.dues16_invoice = True
            member.dues16_invoice_date = invoice_date
        if year == 2017:
            member.dues17_invoice = True
            member.dues17_invoice_date = invoice_date
        if year == 2018:
            member.dues18_invoice = True
            member.dues18_invoice_date = invoice_date
        if year == 2019:
            member.dues19_invoice = True
            member.dues19_invoice_date = invoice_date
        if year == 2020:
            member.dues20_invoice = True
            member.dues20_invoice_date = invoice_date
        if year == 2021:
            member.dues21_invoice = True
            member.dues21_invoice_date = invoice_date
        DBSession().flush()

    @staticmethod
    def _get_dues_invoice_class(year):
        """
        Get the dues invoice class for creating a database record

        TODO: This is only a workaround until the data model has been cleaned
        up and there is an extra table to record dues per year and member.
        """
        year_classes = {
            2015: Dues15Invoice,
            2016: Dues16Invoice,
            2017: Dues17Invoice,
            2018: Dues18Invoice,
            2019: Dues19Invoice,
            2020: Dues20Invoice,
            2021: Dues21Invoice,
        }
        return year_classes[year]

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
        invoice = None
        db_session = DBSession()
        year_class = cls._get_year_class(year)
        if year_class is not None:
            invoice = db_session \
                .query(year_class) \
                .filter(year_class.token == token) \
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
            Sums of the normale and reversal invoices per calendar month based
            on the invoice date.
        """
        year_class = cls._get_year_class(year)
        if year_class is None:
            return None

        db_session = DBSession()
        result = []

        # SQLite specific: substring for SQLite as it does not support
        # date_trunc.
        # invoice_date_month = func.date_trunc(
        #     'month',
        #     invoice_date)
        paid_date = cls._PAYMENT_FIELDS[year]['paid_date']
        amount_paid = cls._PAYMENT_FIELDS[year]['amount_paid']
        invoice_date_month = func.substr(year_class.invoice_date, 1, 7)
        payment_date_month = func.substr(paid_date, 1, 7)

        # collect the invoice amounts per month
        invoice_amounts_query = db_session.query(
            invoice_date_month.label('month'),
            func.sum(
                expression.case(
                    [(expression.not_(
                        year_class.is_reversal), year_class.invoice_amount)],
                    else_=Decimal('0.0'))).label('amount_invoiced_normal'),
            func.sum(
                expression.case(
                    [(year_class.is_reversal, year_class.invoice_amount)],
                    else_=Decimal('0.0'))).label('amount_invoiced_reversal'),
            expression.literal_column('\'0.0\'', DatabaseDecimal).label(
                'amount_paid')).group_by(invoice_date_month)

        # collect the payments per month
        member_payments_query = db_session.query(
            payment_date_month.label('month'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal).label('amount_invoiced_normal'),
            expression.literal_column(
                '\'0.0\'', DatabaseDecimal
            ).label('amount_invoiced_reversal'),
            func.sum(amount_paid).label('amount_paid')
        ).filter(paid_date.isnot(None)) \
            .group_by(payment_date_month)

        # union invoice amounts and payments
        union_all_query = expression.union_all(member_payments_query,
                                               invoice_amounts_query)

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
