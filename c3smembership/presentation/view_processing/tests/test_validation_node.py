# -*- coding: utf-8 -*-
"""
Test the validation_node module
"""

from unittest import TestCase

import colander
from mock import Mock

from c3smembership.presentation.view_processing.validation_node import (
    deferred_preparer,
    deferred_validator,
    ValidationNode,
)


class TestDeferredMethods(TestCase):
    """
    Test the methods deferred_preparer and deferred_validator
    """

    def test_deferred_preparer(self):
        """
        Test the deferred_preparer method
        """
        node = Mock()
        node.transform.side_effect = ['transform result']
        keywords = {'request': 'some request'}

        preparer = deferred_preparer(node, keywords)
        result = preparer('some value')

        node.transform.assert_called_with('some request', 'some value')
        self.assertEquals(result, 'transform result')
        self.assertEquals(node.original_value, 'some value')

    def test_deferred_validator(self):
        """
        Test the deferred_validator method

        1. Test successful validation
        2. Test validation failure
        """
        # 1. Test successful validation
        node = Mock()
        node.validate.side_effect = [None]
        keywords = {'request': 'some request'}

        validator = deferred_validator(node, keywords)
        validator(node, 'some value')

        node.validate.assert_called_with('some request', 'some value')

        # 2. Test validation failure
        node = Mock()
        node.validate.side_effect = ['failure']
        keywords = {'request': 'some request'}

        validator = deferred_validator(node, keywords)
        with self.assertRaises(colander.Invalid):
            validator(node, 'some value')

        node.validate.assert_called_with('some request', 'some value')


class TestValidationNode(TestCase):
    """
    Test the ValidationNode class
    """

    def test_transform(self):
        """
        Test the transform method
        """
        node = ValidationNode(colander.Int)
        result = node.transform(None, 'some value')
        self.assertEquals(result, 'some value')

    def test_validate(self):
        """
        Test the validate method

        1. Test value not None
        2. Test value None
        3. Test custom error message
        """
        # 1. Test value not None
        node = ValidationNode(colander.Int)
        result = node.validate(None, 'some value')
        self.assertIsNone(result)

        # 2. Test value None
        node = ValidationNode(colander.Int)
        with self.assertRaises(colander.Invalid):
            result = node.validate(None, None)

        self.assertIsNone(result)

        # 3. Test custom error message
        node = ValidationNode(colander.Int)
        node.message = 'some error text for value "{}"'
        node.original_value = 'my original value'
        with self.assertRaises(colander.Invalid) as invalid:
            result = node.validate(None, None)

        invalid.node = node
        invalid.message = 'some error text for value "my original value"'

        self.assertIsNone(result)
