# -*- coding: utf-8 -*-
"""
Test the view_processing module
"""

from unittest import TestCase

import mock

from c3smembership.presentation.view_processing import (
    includeme,
    set_colander_error_handler,
    processing_deriver,
)


class TestViewProcessing(TestCase):
    """
    Test the view_processing module
    """

    def test_processing_deriver(self):
        """
        Test the processing_deriver method

        1. Setup
        2. Test without pre- and post-processor
        3. Test pre-processor without result
        4. Test pre-processor with result
        5. Test post-processor without result
        6. Test post-processor with result
        """
        # 1. Setup
        view = mock.Mock()
        info = mock.Mock()
        info.options = {
            'pre_processor': None,
            'post_processor': None
        }
        context = mock.Mock()
        request = mock.Mock()
        pre_processor = mock.Mock()
        post_processor = mock.Mock()

        # 2. Test without pre- and post-processor
        view.side_effect = ['view result']

        view_wrapper = processing_deriver(view, info)
        result = view_wrapper(context, request)

        self.assertEqual(result, 'view result')

        # 3. Test pre-processor without result
        view.side_effect = ['view result']
        info.options['pre_processor'] = pre_processor
        info.options['post_processor'] = None
        pre_processor.side_effect = [None]

        view_wrapper = processing_deriver(view, info)
        result = view_wrapper(context, request)

        pre_processor.assert_called_with(context, request)
        self.assertEqual(result, 'view result')

        # 4. Test pre-processor with result
        view.side_effect = ['view result']
        info.options['pre_processor'] = pre_processor
        info.options['post_processor'] = None
        pre_processor.side_effect = ['pre-processor side effect']

        view_wrapper = processing_deriver(view, info)
        result = view_wrapper(context, request)

        pre_processor.assert_called_with(context, request)
        self.assertEqual(result, 'pre-processor side effect')

        # 5. Test post-processor without result
        view.side_effect = ['view result']
        info.options['pre_processor'] = None
        info.options['post_processor'] = post_processor
        post_processor.side_effect = [None]

        view_wrapper = processing_deriver(view, info)
        result = view_wrapper(context, request)

        post_processor.assert_called_with('view result', context, request)
        self.assertEqual(result, 'view result')

        # 6. Test post-processor with result
        view.side_effect = ['view result']
        info.options['pre_processor'] = None
        info.options['post_processor'] = post_processor
        post_processor.side_effect = ['post-processor side effect']

        view_wrapper = processing_deriver(view, info)
        result = view_wrapper(context, request)

        post_processor.assert_called_with('view result', context, request)
        self.assertEqual(result, 'post-processor side effect')

    def test_set_colander_error_handler(self):
        """
        Test the set_colander_error_handler method
        """
        config = mock.Mock()
        config.registry.view_processing = {}
        error_handler = mock.Mock()

        set_colander_error_handler(config, error_handler)

        self.assertEqual(
            config.registry.view_processing['error_handler'], error_handler)

    def test_includeme(self):
        """
        Test teh includeme method
        """
        config = mock.Mock()

        includeme(config)

        config.add_directive.assert_called_with(
            'set_colander_error_handler', set_colander_error_handler)
        config.add_view_deriver.assert_called_with(processing_deriver)
        self.assertEqual(config.registry.view_processing, {})
