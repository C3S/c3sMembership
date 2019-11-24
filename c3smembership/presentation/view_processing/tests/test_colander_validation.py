# -*- coding: utf-8 -*-
"""
Test the colander_validation module
"""

from unittest import TestCase

import colander
import mock

from c3smembership.presentation.view_processing.colander_validation import (
    ColanderGetValidator,
    ColanderMatchdictValidator,
    ColanderPostValidator,
    ColanderValidator,
)


class DummyColanderValidator(ColanderValidator):
    """
    Dummy implementation of the ColanderValidator class overwriting abstract
    methods
    """
    # pylint: disable=too-few-public-methods

    def get_data(self, request):
        """
        Dummy overwrite of the abstract get_data method
        """
        return request.get_data

    def set_data(self, request, data):
        """
        Dummy overwrite of the abstract set_data method
        """
        request.set_data = data


class TestColanderValidator(TestCase):
    """
    Test the ColanderValidator class
    """

    def test_init(self):
        """
        Test the ColanderValidator constructor
        """
        validator = ColanderValidator('schema', 'error_handler')
        self.assertEqual(validator.schema, 'schema')
        self.assertEqual(validator.error_handler, 'error_handler')

    def test_call(self):
        """
        Test the __call__ method

        1. Validation success
        2. Validation failure with forwarded exception
        3. Validation failure with node error handler
        4. Validation failure with schema error handler
        5. Validation failure with settings error handler
        6. Validation success with node renaming
        """
        # pylint: disable=too-many-statements
        schema_bind = mock.Mock()
        schema = mock.Mock(spec=['children', 'bind'])
        schema.children = []
        context = mock.Mock()
        request = mock.Mock()
        node = mock.Mock()
        node.asdict.side_effect = []
        node.name = 'node name'
        request.get_data = 'get data'
        request.registry.view_processing = {}

        # 1. Validation success
        schema_bind.deserialize.side_effect = ['data']
        schema.bind.side_effect = [schema_bind]

        validator = DummyColanderValidator(schema)
        result = validator(context, request)

        self.assertIsNone(result)
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(request.set_data, 'data')

        # 2. Validation failure with forwarded exception
        schema_bind.deserialize.side_effect = [colander.Invalid(node, 'abc')]
        schema.bind.side_effect = [schema_bind]

        validator = DummyColanderValidator(schema)

        with self.assertRaises(colander.Invalid) as raise_context:
            result = validator(context, request)

        self.assertIsNone(result)
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(raise_context.exception.node, node)
        self.assertEqual(raise_context.exception.msg, 'abc')

        # 3. Validation failure with node error handler
        error_handler = mock.Mock()
        error_handler.side_effect = ['error handler result']
        schema_bind.deserialize.side_effect = [colander.Invalid(node, 'abc')]
        schema.bind.side_effect = [schema_bind]

        validator = DummyColanderValidator(schema, error_handler)
        result = validator(context, request)

        self.assertEquals(result, 'error handler result')
        error_handler.assert_called_with(request, schema, {'node name': 'abc'})
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(raise_context.exception.node, node)
        self.assertEqual(raise_context.exception.msg, 'abc')

        # 4. Validation failure with schema error handler
        error_handler = mock.Mock()
        error_handler.side_effect = ['error handler result']
        schema_bind.deserialize.side_effect = [colander.Invalid(node, 'abc')]
        schema.bind.side_effect = [schema_bind]
        schema.error_handler = error_handler

        validator = DummyColanderValidator(schema)
        result = validator(context, request)

        self.assertEquals(result, 'error handler result')
        error_handler.assert_called_with(request, schema, {'node name': 'abc'})
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(raise_context.exception.node, node)
        self.assertEqual(raise_context.exception.msg, 'abc')

        # 5. Validation failure with settings error handler
        error_handler = mock.Mock()
        error_handler.side_effect = ['error handler result']
        schema_bind = mock.Mock()
        schema_bind.deserialize.side_effect = [colander.Invalid(node, 'abc')]
        schema = mock.Mock(spec=['children', 'bind'])
        schema.bind.side_effect = [schema_bind]
        request.registry.view_processing['error_handler'] = error_handler

        validator = DummyColanderValidator(schema)
        result = validator(context, request)

        self.assertEquals(result, 'error handler result')
        error_handler.assert_called_with(request, schema, {'node name': 'abc'})
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(raise_context.exception.node, node)
        self.assertEqual(raise_context.exception.msg, 'abc')

        # 6. Validation success with node renaming
        node = mock.Mock()
        node.name = 'original node name'
        node.new_name = 'new node name'
        schema = mock.Mock(spec=['children', 'bind'])
        schema_bind.deserialize.side_effect = [{node.name: 'data'}]
        schema.bind.side_effect = [schema_bind]
        schema.children = [node]

        validator = DummyColanderValidator(schema)
        result = validator(context, request)

        self.assertIsNone(result)
        schema.bind.assert_called_with(request=request)
        schema_bind.deserialize.assert_called_with('get data')
        self.assertEqual(request.set_data, {'new node name': 'data'})

    def test_get_data(self):
        """
        Test the get_data method
        """
        validator = ColanderValidator(None)
        with self.assertRaises(NotImplementedError):
            validator.get_data(None)

    def test_set_data(self):
        """
        Test the set_data method
        """
        validator = ColanderValidator(None)
        with self.assertRaises(NotImplementedError):
            validator.set_data(None, None)


class TestColanderMatchdictValidator(TestCase):
    """
    Test the ColanderMatchdictValidator class
    """

    def test_get_data(self):
        """
        Test the get_data method
        """
        request = mock.Mock()
        request.matchdict = 'test matchdict'
        validator = ColanderMatchdictValidator(None)
        result = validator.get_data(request)
        self.assertEqual(result, 'test matchdict')

    def test_set_data(self):
        """
        Test the set_data method
        """
        request = mock.Mock()
        request.validated_matchdict = None
        validator = ColanderMatchdictValidator(None)
        validator.set_data(request, 'data')
        self.assertEqual(request.validated_matchdict, 'data')


class TestColanderPostValidator(TestCase):
    """
    Test the ColanderPostValidator class
    """

    def test_get_data(self):
        """
        Test the get_data method
        """
        request = mock.Mock()
        request.POST = 'test matchdict'
        validator = ColanderPostValidator(None)
        result = validator.get_data(request)
        self.assertEqual(result, 'test matchdict')

    def test_set_data(self):
        """
        Test the set_data method
        """
        request = mock.Mock()
        request.validated_post = None
        validator = ColanderPostValidator(None)
        validator.set_data(request, 'data')
        self.assertEqual(request.validated_post, 'data')


class TestColanderGetValidator(TestCase):
    """
    Test the ColanderPostValidator class
    """

    def test_get_data(self):
        """
        Test the get_data method
        """
        request = mock.Mock()
        request.GET = 'test matchdict'
        validator = ColanderGetValidator(None)
        result = validator.get_data(request)
        self.assertEqual(result, 'test matchdict')

    def test_set_data(self):
        """
        Test the set_data method
        """
        request = mock.Mock()
        request.validated_get = None
        validator = ColanderGetValidator(None)
        validator.set_data(request, 'data')
        self.assertEqual(request.validated_get, 'data')
