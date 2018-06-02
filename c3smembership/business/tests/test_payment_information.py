# -*- coding: utf-8 -*-
"""
Test the payment information module.
"""

from unittest import TestCase

import mock

from c3smembership.business.payment_information import (
    PaymentInformation,
)


class PaymentInformationTest(TestCase):
    """
    Test the PaymentInformation class.
    """

    def test_get_payments(self):
        """
        Test the get_payments method.
        """
        payment_repository_mock = mock.Mock()
        payment_repository_mock.get_payments.side_effect = [
            'get_payments result']

        payment_information = PaymentInformation(payment_repository_mock)

        payments = payment_information.get_payments(
            'page_number', 'page_size', 'from_date', 'to_date')

        self.assertEqual(payments, 'get_payments result')
        self.assertTrue(payment_repository_mock.get_payments.called_with((
            'page_number', 'page_size', 'from_date', 'to_date')))
