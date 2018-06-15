# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.views.payment_list package.
"""

import datetime
import unittest

import deform
from mock import Mock
from pyramid import testing

import c3smembership.presentation.views.payment_list as payment_list_package
from c3smembership.presentation.views.payment_list import (
    date_cookie_formatter,
    date_cookie_parser,
    get_filter_from_cookies,
    handle_filtering,
    reset_filtering,
    payment_list,
    payment_content_size_provider,
    set_filters_to_cookies,
)


class TestPaymentList(unittest.TestCase):
    """
    Tests the payment_list and payment_content_size_provider functions
    from the c3smembership.presentation.views.payment_list package.
    """

    def test_reset_filtering(self):
        """
        Tests the reset_filterung function.
        """
        # Reset filter to default
        filtering = {
            'preset': 'filter',
            'from_date': 'from_date some value'
        }
        filter_settings = {
            'from_date': {
                'default': 'from_date default'
            }
        }

        filtering_reset = reset_filtering(filtering, filter_settings)
        self.assertEqual(
            filtering_reset,
            {
                'preset': 'filter',
                'from_date': 'from_date default'
            })

        # Add filter default
        filtering = {
            'preset': 'filter'
        }
        filter_settings = {
            'from_date': {
                'default': 'from_date default'
            }
        }

        filtering_reset = reset_filtering(filtering, filter_settings)
        self.assertEqual(
            filtering_reset,
            {
                'preset': 'filter',
                'from_date': 'from_date default'
            })

    def test_date_cookie_parser(self):
        """
        Tests the date_cookie_parser function.
        """
        # test valid date
        cookie_value = '2018-06-14'
        filter_setting = {
            'date_format': '%Y-%m-%d'
        }
        filter_value = date_cookie_parser(cookie_value, filter_setting)
        self.assertEqual(filter_value, datetime.date(2018, 6, 14))

        # test invalid date default
        cookie_value = '2018-06-14'
        filter_setting = {
            'date_format': '%Y%m%d',
            'default': 'some_default_date'
        }
        filter_value = date_cookie_parser(cookie_value, filter_setting)
        self.assertEqual(filter_value, 'some_default_date')

        # test invalid date None
        cookie_value = '2018-06-14'
        filter_setting = {
            'date_format': '%Y%m%d'
        }
        filter_value = date_cookie_parser(cookie_value, filter_setting)
        self.assertEqual(filter_value, None)

    def test_date_cookie_formatter(self):
        """
        Tests the date_cookie_formatter function.
        """
        filter_setting = {
            'date_format': '%Y-%m-%d'
        }
        filter_value = datetime.date(2018, 6, 14)
        cookie_value = date_cookie_formatter(filter_value, filter_setting)
        self.assertEqual(cookie_value, '2018-06-14')

        filter_setting = {
            'date_format': None
        }
        filter_value = datetime.date(2018, 6, 14)
        cookie_value = date_cookie_formatter(filter_value, filter_setting)
        self.assertEqual(cookie_value, None)

    def test_get_filter_from_cookies(self):
        """
        Tests the get_filter_from_cookies function.
        """

        def dummy_parser(value, filter_setting):
            # pylint: disable=unused-argument
            """
            Dummy type parser.
            """
            return u'dummy parser result'

        filter_settings = {
            'from_date': {
                'type': 'test_type',
                'default': 'default value',
            }
        }
        cookie_parsers = {
            'test_type': dummy_parser
        }

        filtering = {'preset': 'filter'}
        request_dummy = testing.DummyRequest(
            cookies = {u'payment_list.from_date': u'from_date value'})
        filtering = get_filter_from_cookies(
            request_dummy, filtering, filter_settings, cookie_parsers)
        self.assertEqual(
            filtering,
            {
                'from_date': 'dummy parser result',
                'preset': 'filter'
            })

    def test_handle_filtering(self):
        """
        Tests the handle_filtering function.
        """

        def dummy_cookie_parser(cookie_value, filter_setting):
            # pylint: disable=unused-argument
            """
            Dummy cookie parser.
            """
            return u'parsing result'

        def dummy_cookie_formatter(filter_value, filter_setting):
            # pylint: disable=unused-argument
            """
            Dummy cookie formatter.
            """
            return 'formatted_result'

        cookie_parsers = {
            'date': dummy_cookie_parser
        }
        cookie_formatters = {
            'date': dummy_cookie_formatter
        }
        filter_settings = {
            'from_date': {
                'type': 'date',
                'default': None,
            }
        }

        # Test no form action
        request_dummy = testing.DummyRequest(
            cookies={u'payment_list.from_date': u'from date value'})
        request_dummy.POST = {}
        filter_form = Mock()
        filter_form.render.side_effect = ['filter form render result']

        filter_form, filtering = handle_filtering(
            request_dummy,
            filter_form,
            filter_settings,
            {},
            cookie_parsers,
        )
        self.assertEqual(filter_form, 'filter form render result')
        self.assertEqual(filtering, {'from_date': 'parsing result'})

        # Test reset
        request_dummy = testing.DummyRequest(
            cookies={u'payment_list.from_date': u'from date value'},
            post={'reset': 'reset'})
        filter_form = Mock()
        filter_form.render.side_effect = ['filter form render result']

        filter_form, filtering = handle_filtering(
            request_dummy,
            filter_form,
            filter_settings,
            cookie_formatters,
            cookie_parsers,
        )
        self.assertEqual(filter_form, 'filter form render result')
        self.assertEqual(filtering, {'from_date': None})

        # Test submit with successful validation
        request_dummy = testing.DummyRequest(
            post={'submit': 'submit'},
            cookies={u'payment_list.from_date': u'from date value'})
        filter_form = Mock()
        filter_form.render.side_effect = ['filter form render result']
        filter_form.validate.side_effect = [filtering]

        filter_form, filtering = handle_filtering(
            request_dummy,
            filter_form,
            filter_settings,
            cookie_formatters,
            cookie_parsers,
        )
        self.assertEqual(filter_form, 'filter form render result')
        self.assertEqual(filtering, {'from_date': None})

        # Test submit with validation failure
        request_dummy = testing.DummyRequest(
            post={'submit': 'submit'},
            cookies={u'payment_list.from_date': u'from date value'})
        filter_form = Mock()
        mock_field = Mock()
        filter_form.render.side_effect = [deform.ValidationFailure(
            mock_field,
            filtering,
            'error')]
        filter_form.validate.side_effect = ['validation result']

        filter_form, filtering = handle_filtering(
            request_dummy,
            filter_form,
            filter_settings,
            cookie_formatters,
            cookie_parsers,
        )
        self.assertEqual(filter_form, mock_field.widget.serialize())
        self.assertEqual(filtering, 'validation result')


    def test_set_filters_to_cookies(self):
        # pylint: disable=no-self-use
        """
        Tests the set_filters_to_cookies function.
        """
        def dummy_cookie_formatter(value, filter_setting):
            # pylint: disable=unused-argument
            """
            Dummy cookie formatter.
            """
            return 'formatted value'

        request_dummy = testing.DummyRequest()
        request_dummy.response.set_cookie = Mock()
        filtering = {
            'preset': 'filter',
            'from_date': 'test value'
        }
        filter_settings = {
            'from_date': {
                'type': 'test_type'
            }
        }
        cookie_formatters = {
            'test_type': dummy_cookie_formatter
        }

        set_filters_to_cookies(
            request_dummy, filtering, filter_settings, cookie_formatters)
        request_dummy.response.set_cookie.assert_called_with(
            'payment_list.from_date',
            value='formatted value')

    def test_payment_list(self):
        """
        Tests the payment_list function.
        """
        # TODO: Dependency injection the dirty way. It's working but indicates
        # a design issue. Refactoring is required.
        original_filter_form = \
            payment_list_package.FILTER_FORM
        payment_list_package.FILTER_FORM = Mock()

        # Test member found
        payment_information_dummy = Mock()
        payment_information_dummy.get_payments.side_effect = ['payment list']
        payment_information_dummy.get_payment_count.side_effect = [1]
        request_dummy = testing.DummyRequest()
        request_dummy.registry.payment_information = payment_information_dummy
        request_dummy.pagination = Mock()
        request_dummy.pagination.paging.page_number = 12
        request_dummy.pagination.paging.page_size = 23
        request_dummy.pagination.sorting.sort_property = 'sort property'
        request_dummy.pagination.sorting.sort_direction = 'sort direction'

        result = payment_list(request_dummy)

        self.assertEqual(result['payments'], 'payment list')
        payment_information_dummy.get_payments.assert_called_with(
            12,
            23,
            'sort property',
            'sort direction',
            None,
            None
        )

        # TODO: Cleanup dirty dependency injection. It's working but indicates
        # a design issue. Refactoring is required.
        payment_list_package.FILTER_FORM = \
            original_filter_form

    # pylint: disable=invalid-name
    def test_payment_content_size_provider(self):
        """
        Tests the payment_list function.
        """
        # TODO: Dependency injection the dirty way. It's working but indicates
        # a design issue. Refactoring is required.
        original_filter_form = \
            payment_list_package.FILTER_FORM
        payment_list_package.FILTER_FORM = Mock()

        # Prepare
        payment_information_dummy = Mock()
        payment_information_dummy.get_payment_count.side_effect = [42]
        request_dummy = testing.DummyRequest()
        request_dummy.registry.payment_information = payment_information_dummy
        request_dummy.localizer = Mock()

        # Test
        result = payment_content_size_provider(request_dummy)
        self.assertEqual(result, 42)

        # TODO: Cleanup dirty dependency injection. It's working but indicates
        # a design issue. Refactoring is required.
        payment_list_package.FILTER_FORM = \
            original_filter_form
