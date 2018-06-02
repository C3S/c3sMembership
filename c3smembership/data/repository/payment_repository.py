# -*- coding: utf-8  -*-
"""
Repository for accessing payments
"""

import datetime
from decimal import Decimal

from c3smembership.data.model.base import DBSession
from c3smembership.models import C3sMember


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
    def _sort_payments(cls, payments):
        """
        Sorts the payments ascending by date and membership number-
        """
        return sorted(payments, key=lambda k: (
            k['date'],
            k['membership_number']))

    @classmethod
    def _slice_payments(cls, payments, page_number, page_size):
        """
        Slices the payments to the given page number according to the page
        size.
        """
        first_index = cls._get_first_index(page_number, page_size)
        last_index = cls._get_last_index(page_number, page_size)
        return payments[first_index:last_index]

    @classmethod
    def get_payments(
            cls, page_number, page_size, from_date=None, to_date=None):
        """
        Gets the payments for a page filtered by dates.

        Args:
            page_number: The number of the page of payments to be returned.
            page_size: The size of the pages of payments.
            from_date: Optional. The earliest payment date. All older payments
                are filtered.
            to_date: Optional. The latest payment date. All younger payments
                are filtered.
        """
        payments = []
        members = DBSession().query(C3sMember).all()

        # Collect payments
        payments = payments + cls._get_dues15_payments(members)
        payments = payments + cls._get_dues16_payments(members)
        payments = payments + cls._get_dues17_payments(members)

        # Arrange payments
        payments = cls._filter_payments(payments, from_date, to_date)
        payments = cls._sort_payments(payments)
        payments = cls._slice_payments(payments, page_number, page_size)

        return payments
