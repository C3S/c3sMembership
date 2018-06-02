# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.views.payment_list package.
"""

import unittest

from mock import Mock
from pyramid import testing

import c3smembership.presentation.views.payment_list as payment_list_package
from c3smembership.presentation.views.payment_list import (
    payment_list,
    payment_content_size_provider,
)


class PaymentInformationDummy(object):
    """
    Dummy to simulate the
    c3smembership.business.payment_information.PaymentInformation class.
    """

    def __init__(self, result):
        """
        Initialises the PaymentInformationDummy object.

        Args:
            result: The value to be returned on the get_payments() call.
        """
        self._result = result
        self._page_number = None
        self._page_size = None

    def get_payments(self, page_number, page_size):
        """
        Gets the payments.

        Args:
            page_number: The page number which can be retrieved from the
                get_page_number method.
            page_size: The page size which can be retrieved from the
                get_page_size method.
        """
        self._page_number = page_number
        self._page_size = page_size
        return self._result

    def get_page_number(self):
        """
        Gets the page number passed to the get_payments method.
        """
        return self._page_number

    def get_page_size(self):
        """
        Gets the page size passed to the get_payments method.
        """
        return self._page_size


class TestPaymentList(unittest.TestCase):
    """
    Tests the payment_list and payment_content_size_provider functions
    from the c3smembership.presentation.views.payment_list package.
    """

    def test_payment_list(self):
        """
        Tests the payment_list function.
        """
        # test member found
        payment_information_dummy = PaymentInformationDummy('payment list')
        request_dummy = testing.DummyRequest()
        request_dummy.registry.payment_information = payment_information_dummy
        request_dummy.pagination = Mock()
        request_dummy.pagination.paging.page_number = 12
        request_dummy.pagination.paging.page_size = 23

        result = payment_list(request_dummy)

        self.assertEqual(result, {'payments': 'payment list'})
        self.assertEqual(payment_information_dummy.get_page_number(), 12)
        self.assertEqual(payment_information_dummy.get_page_size(), 23)

    # pylint: disable=invalid-name
    def test_payment_content_size_provider(self):
        """
        Tests the payment_list function.
        """

        # Dependency injection the dirty way
        original_payment_information = payment_list_package.PaymentInformation
        original_payment_repository = payment_list_package.PaymentRepository

        payment_repository_dummy = Mock()
        payment_information_dummy = Mock()
        payment_information_dummy.get_payments.side_effect = [[
            'one payment',
            'another payment']]
        payment_information_class_dummy = Mock()
        payment_information_class_dummy.side_effect = \
            [payment_information_dummy]
        payment_list_package.PaymentInformation = \
            payment_information_class_dummy
        payment_list_package.PaymentRepository = payment_repository_dummy

        # test
        result = payment_content_size_provider()
        self.assertTrue(payment_information_class_dummy.calledWith(
            payment_list_package.PaymentRepository))
        self.assertTrue(payment_information_dummy.get_payments.calledWith(
            1,
            1000000000))
        self.assertEqual(result, 2)

        # Cleanup dirty dependency injection
        payment_list_package.PaymentInformation = original_payment_information
        payment_list_package.PaymentRepository = original_payment_repository
