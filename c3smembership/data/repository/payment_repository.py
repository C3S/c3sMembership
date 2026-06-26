# -*- coding: utf-8  -*-
"""
Repository for accessing payments
"""

import datetime
from decimal import Decimal

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base import DBSession


# pylint: disable=too-few-public-methods
class PaymentRepository(object):
    """
    Repository for accessing payments.
    """

    @classmethod
    def _create_payment(
            cls, date, account, reference, membership_number, firstname,
            lastname, amount):
        # pylint: disable=too-many-arguments
        """
        Creates a payment record.
        """
        return {
            'date': date,
            'account': account,
            'reference': reference,
            'membership_number': membership_number,
            'firstname': firstname,
            'lastname': lastname,
            'amount': amount,
        }

    @classmethod
    def _get_dues_payments(cls, members):
        """
        Gets all dues payments from the members across all years.

        Payments are grouped year by year (ascending) and, within a year, follow
        the order of the members passed in.
        """
        payments_by_year = {}
        for member in members:
            for dues in member.dues:
                if dues.paid:
                    payments_by_year.setdefault(dues.year, []).append(
                        cls._create_payment(
                            date=dues.paid_date.date(),
                            account='Membership dues {0}'.format(dues.year),
                            reference=dues.token,
                            membership_number=member.membership_number,
                            firstname=member.firstname,
                            lastname=member.lastname,
                            amount=Decimal(dues.amount_paid)))
        payments = []
        for year in sorted(payments_by_year):
            payments += payments_by_year[year]
        return payments

    @classmethod
    def _get_first_index(cls, page_number, page_size):
        """
        Gets the first index for slicing on indices from page number and page
        size.
        """
        return (page_number - 1) * page_size

    @classmethod
    def _get_last_index(cls, page_number, page_size):
        """
        Gets the last index for slicing on indices from page number and page
        size.
        """
        return page_number * page_size

    @classmethod
    def _filter_payments(cls, payments, from_date, to_date):
        """
        Filters the payments returning all payments occurred on or later than
        the from date and earlier or the latest on to date.
        """
        if from_date is not None or to_date is not None:
            if from_date is None:
                from_date = datetime.date(1, 1, 1)
            if to_date is None:
                to_date = datetime.date(9999, 1, 1)
            # pylint: disable=bad-builtin,deprecated-lambda
            payments = [k for k in payments if k['date'] >= from_date and k['date'] <= to_date]
        return payments

    @classmethod
    def _sort_payments(cls, payments, sort_property, sort_direction):
        """
        Sorts the payments by sort property in sort direction.

        Args:
            payments: The payment list to be sorted.
            sort_property: A string representing the payment property by which
                the payment list is sorted.
            sort_direction: A string representing the sort direction, either
                "asc" for ascending sorting or "desc" for descending sorting.
        """
        reverse = True if sort_direction.lower() == 'desc' else False
        return sorted(
            payments,
            key=lambda k: k[sort_property],
            reverse=reverse)

    @classmethod
    def _slice_payments(cls, payments, page_number=None, page_size=None):
        """
        Slices the payments to the given page number according to the page
        size.

        If page number or page size are not specified then all available items
        are returned without any slicing applied.

        Args:
            page_number: Optional. Integer specifying the page to be displayed.
            page_size: Optional. Integer specifying the size of a page in terms
                of number of items displayed on the page.

        Returns:
            An array of payments.
        """
        if page_number is not None and page_size is not None:
            first_index = cls._get_first_index(page_number, page_size)
            last_index = cls._get_last_index(page_number, page_size)
            return payments[first_index:last_index]
        else:
            return payments

    @classmethod
    def _is_valid_sort_property(cls, sort_property):
        return sort_property in [
            'date',
            'account',
            'reference',
            'membership_number',
            'firstname',
            'lastname',
            'amount',
        ]

    # pylint: disable=too-many-arguments
    @classmethod
    def get_payments(
            cls, page_number=None, page_size=None, sort_property='date',
            sort_direction='asc', from_date=None, to_date=None):
        """
        Gets the payments for a page filtered by dates.

        If page number or page size are not specified then all available items
        are returned without any slicing applied.

        Args:
            page_number: Optional. The number of the page of payments to be
                returned.
            page_size: Optional. The size of the pages of payments.
            sort_property: Optional. A string representing the payment property
                by which the payment list is sorted. Valid sort properties are:

                - date
                - account
                - reference
                - membership_number
                - firstname
                - lastname
                - amount

                The default sort property is "date".
            sort_direction: Optional. A string representing the sort direction,
                either "asc" for ascending sorting or "desc" for descending
                sorting. The default sort direction is ascending.
            from_date: Optional. The earliest payment date. All older payments
                are filtered.
            to_date: Optional. The latest payment date. All younger payments
                are filtered.

        Raises:
            ValueError: In case sort_property is not valid.
        """
        if not cls._is_valid_sort_property(sort_property):
            raise ValueError(
                '"{}"" is an invalid sort property.'.format(
                    str(sort_property)))

        members = DBSession().query(C3sMember).all()

        # Collect payments
        payments = cls._get_dues_payments(members)

        # Arrange payments
        payments = cls._filter_payments(payments, from_date, to_date)
        payments = cls._sort_payments(payments, sort_property, sort_direction)
        payments = cls._slice_payments(payments, page_number, page_size)

        return payments

    def get_payment_count(self, from_date=None, to_date=None):
        """
        Gets the count of payments of which the payment date is not older than
        from date and not younger than to date.

        Args:
            from_date: Optional. A datetime.date specifying the oldest payment
                date for payments to be counted.
            to_date: Optional. A datetie.date specifying the youngest payment
                date for payments to be counted.

        Return:
            An integer representing the count of payments available not older
            than from date and not younger than to date.
        """
        return len(self.get_payments(
            from_date=from_date,
            to_date=to_date))
