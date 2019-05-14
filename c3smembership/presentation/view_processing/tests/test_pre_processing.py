# -*- coding: utf-8 -*-
"""
Test the pre_processing module
"""

from unittest import TestCase

import mock

from c3smembership.presentation.view_processing.pre_processing import (
    PreProcessor,
    MultiPreProcessor,
)


class TestpreProcessor(TestCase):
    """
    Test the preProcessor class
    """

    def test_call(self):
        """
        Test the __call__ method
        """
        processor = PreProcessor()
        with self.assertRaises(NotImplementedError):
            processor(None, None)


class TestMultiPreProcessor(TestCase):
    """
    Test the MultiPreProcessor class
    """

    def test(self):
        """
        Test the __init__ and __call__ methods

        1. Processors without result
        2. Processors with result
        """
        # 1. Processors without result
        proc1 = mock.Mock()
        proc1.side_effect = [None]
        proc2 = mock.Mock()
        proc2.side_effect = [None]
        processor = MultiPreProcessor([proc1, proc2])
        result = processor('context', 'request')
        self.assertIsNone(result)

        # 2. Processors with result
        proc1 = mock.Mock()
        proc1.side_effect = ['proc1 result']
        proc2 = mock.Mock()
        proc2.side_effect = [None]
        processor = MultiPreProcessor([proc1, proc2])
        result = processor('context', 'request')
        self.assertEquals(result, 'proc1 result')
