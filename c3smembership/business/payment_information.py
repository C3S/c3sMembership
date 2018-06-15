# -*- coding: utf-8 -*-
"""
Provides payment information.
"""


# pylint: disable=too-few-public-methods
class PaymentInformation(object):
    """
    Provides payment information.
    """

    def __init__(self, payment_repository):
        """
        Initialises the PaymentInformation object.

        Args:
            payment_repository: The payment repository object used to access
                payment data.
        """
        self._payment_repository = payment_repository

    # pylint: disable=too-many-arguments
    def get_payments(
            self, page_number=None, page_size=None, sort_property='date',
            sort_direction='asc', from_date=None, to_date=None):
        """
        Gets the payments for a page filtered by dates.

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
        """
        return self._payment_repository.get_payments(
            page_number,
            page_size,
            sort_property,
            sort_direction,
            from_date,
            to_date)

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
        return self._payment_repository.get_payment_count(from_date, to_date)
