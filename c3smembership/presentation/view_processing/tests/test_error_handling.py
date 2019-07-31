# -*- coding: utf-8 -*-
"""
Test the error_handling module
"""

from unittest import TestCase

import mock

from c3smembership.presentation.view_processing.error_handling import (
    ErrorHandler,
    FlashCallbackErrorHandler,
    FlashErrorHandler,
    MultiErrorHandler,
)


class TestErrorHandler(TestCase):
    """
    Test the ErrorHandler class
    """

    def test_init(self):
        """
        Test the constructor
        """
        handler = ErrorHandler()
        with self.assertRaises(NotImplementedError):
            handler(None, None, None)


class TestMultiErrorHandler(TestCase):
    """
    Test the MultiErrorHandler class
    """

    def test_call(self):
        """
        Test the __call__ method

        1. Error handlers without result
        2. Error handlers with result
        """
        # 1. Error handlers without result
        error_handler1 = mock.Mock()
        error_handler1.side_effect = [None]
        error_handler2 = mock.Mock()
        error_handler2.side_effect = [None]
        error_handler3 = mock.Mock()
        error_handler3.side_effect = [None]
        error_handlers = [error_handler1, error_handler2, error_handler3]
        handler = MultiErrorHandler(error_handlers)

        result = handler('request', 'schema', 'errors')

        self.assertIsNone(result)
        error_handler1.assert_called_with('request', 'schema', 'errors')
        error_handler2.assert_called_with('request', 'schema', 'errors')
        error_handler3.assert_called_with('request', 'schema', 'errors')

        # 2. Error handlers with result
        error_handler1 = mock.Mock()
        error_handler1.side_effect = [None]
        error_handler2 = mock.Mock()
        error_handler2.side_effect = ['error handling result']
        error_handler3 = mock.Mock()
        error_handler3.side_effect = [None]
        error_handlers = [error_handler1, error_handler2, error_handler3]
        handler = MultiErrorHandler(error_handlers)

        result = handler('request', 'schema', 'errors')

        self.assertEquals(result, 'error handling result')
        error_handler1.assert_called_with('request', 'schema', 'errors')
        error_handler2.assert_called_with('request', 'schema', 'errors')
        error_handler3.assert_not_called()


class TestFlashCallbackErrorHandler(TestCase):
    """
    Test the FlashCallbackErrorHandler class
    """

    def test_call(self):
        """
        Test the __call__ method
        """
        callback = mock.Mock()
        callback.side_effect = [None]
        request = mock.Mock()
        handler = FlashCallbackErrorHandler(callback)
        errors = {
            'node 1': 'error 1',
            'node 2': 'error 2',
        }

        result = handler(request, None, errors)

        request.session.flash.assert_any_call('error 1', 'danger')
        request.session.flash.assert_any_call('error 2', 'danger')
        self.assertIsNone(result)


class TestFlashErrorHandler(TestCase):
    """
    Test the FlashErrorHandler class
    """

    def test_call(self):
        """
        Test the __call__ method

        1. No error route
        2. Own error route
        3. Schema error route
        """
        # 1. No error route
        handler = FlashErrorHandler()
        result = handler(None, None, [])
        self.assertIsNone(result)

        # 2. Own error route
        request = mock.Mock()
        request.route_url.side_effect = ['route url']
        handler = FlashErrorHandler('error route')

        result = handler(request, None, [])

        request.route_url.assert_called_with('error route')
        self.assertEquals(result.code, 302)
        self.assertEquals(result.location, 'route url')

        # 3. Schema error route
        request = mock.Mock()
        request.route_url.side_effect = ['route url']
        schema = mock.Mock()
        schema.error_route = 'error route'
        handler = FlashErrorHandler()

        result = handler(request, schema, [])

        request.route_url.assert_called_with('error route')
        self.assertEquals(result.code, 302)
        self.assertEquals(result.location, 'route url')
