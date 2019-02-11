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
    def _get_dues15_payments(cls, members):
        """
        Gets the dues payments for 2015 from the members.
        """
        payments = []
        for member in members:
            if member.dues15_paid:
                payments.append(cls._create_payment(
                    date=member.dues15_paid_date.date(),
                    account=u'Membership dues 2015',
                    reference=member.dues15_token,
                    membership_number=member.membership_number,
                    firstname=member.firstname,
                    lastname=member.lastname,
                    amount=Decimal(member.dues15_amount_paid)))
        return payments

    @classmethod
    def _get_dues16_payments(cls, members):
        """
        Gets the dues payments for 2016 from the members.
        """
        payments = []
        for member in members:
            if member.dues16_paid:
                payments.append(cls._create_payment(
                    date=member.dues16_paid_date.date(),
                    account=u'Membership dues 2016',
                    reference=member.dues16_token,
                    membership_number=member.membership_number,
                    firstname=member.firstname,
                    lastname=member.lastname,
                    amount=Decimal(member.dues16_amount_paid)))
        return payments

    @classmethod
    def _get_dues17_payments(cls, members):
        """
        Gets the dues payments for 2017 from the members.
        """
        payments = []
        for member in members:
            if member.dues17_paid:
                payments.append(cls._create_payment(
                    date=member.dues17_paid_date.date(),
                    account=u'Membership dues 2017',
                    reference=member.dues17_token,
                    membership_number=member.membership_number,
                    firstname=member.firstname,
                    lastname=member.lastname,
                    amount=Decimal(member.dues17_amount_paid)))
        return payments

    @classmethod
    def _get_dues18_payments(cls, members):
        """
        Gets the dues payments for 2018 from the members.
        """
        payments = []
        for member in members:
            if member.dues18_paid:
                payments.append(cls._create_payment(
                    date=member.dues18_paid_date.date(),
                    account=u'Membership dues 2018',
                    reference=member.dues18_token,
                    membership_number=member.membership_number,
                    firstname=member.firstname,
                    lastname=member.lastname,
                    amount=Decimal(member.dues18_amount_paid)))
        return payments

    @classmethod
    def _get_dues19_payments(cls, members):
        """
        Gets the dues payments for 2019 from the members.
        """
        payments = []
        for member in members:
            if member.dues19_paid:
                payments.append(cls._create_payment(
                    date=member.dues19_paid_date.date(),
                    account=u'Membership dues 2019',
                    reference=member.dues19_token,
                    membership_number=member.membership_number,
                    firstname=member.firstname,
                    lastname=member.lastname,
                    amount=Decimal(member.dues19_amount_paid)))
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
            payments = filter(
                lambda k: k['date'] >= from_date and k['date'] <= to_date,
                payments)
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
                u'"{}"" is an invalid sort property.'.format(
                    unicode(sort_property)))

        payments = []
        members = DBSession().query(C3sMember).all()

        # Collect payments
        payments = payments + cls._get_dues15_payments(members)
        payments = payments + cls._get_dues16_payments(members)
        payments = payments + cls._get_dues17_payments(members)
        payments = payments + cls._get_dues18_payments(members)
        payments = payments + cls._get_dues19_payments(members)

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
