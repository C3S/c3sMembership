# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.schemas.general_assembly module
"""

from unittest import TestCase

from colander import (
    Invalid,
    MappingSchema,
)
from mock import Mock

from c3smembership.presentation.schemas.general_assembly import (
    GeneralAssemblyFormFactory,
    GeneralAssemblyNode,
    GeneralAssemblySchema,
)


class DummySchema(MappingSchema):
    """
    Dummy schema for testing the GeneralAssemblyNode class
    """
    general_assembly_number = GeneralAssemblyNode()


class TestGeneralAssemblyNode(TestCase):
    """
    Test the GeneralAssemblyNode class
    """

    def test_integration(self):
        """
        Integration test the GeneralAssemblyNode

        1. Success
        2. Failure, invalid number
        3. Failure, general assembly not found
        """
        # Setup
        request = Mock()
        schema = DummySchema()

        # 1. Success
        request \
            .registry \
            .general_assembly_invitation \
            .get_general_assembly \
            .side_effect = ['some general assembly']

        data = schema \
            .bind(request=request) \
            .deserialize({'general_assembly_number': '123'})

        self.assertEqual(
            data['general_assembly_number'], 'some general assembly')

        # 2. Failure, invalid number
        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'general_assembly_number': 'asdf'})

        self.assertEqual(
            invalid.exception.asdict()['general_assembly_number'],
            u'"asdf" is not a number')

        # 3. Failure, general assembly not found
        request \
            .registry \
            .general_assembly_invitation \
            .get_general_assembly \
            .side_effect = [None]

        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'general_assembly_number': '987'})

        self.assertEqual(
            invalid.exception.asdict()['general_assembly_number'],
            u'General assembly 987 does not exist.')

    def test_transform(self):
        """
        Test the transform method
        """
        request = Mock()
        request \
            .registry \
            .general_assembly_invitation \
            .get_general_assembly \
            .side_effect = ['some general assembly']
        node = GeneralAssemblyNode()
        result = node.transform(request, 'some value')

        self.assertEqual(result, 'some general assembly')
        request \
            .registry \
            .general_assembly_invitation \
            .get_general_assembly \
            .assert_called_with('some value')


class TestGeneralAssemblyFormFactory(TestCase):
    """
    Test the GeneralAssemblyFormFactory class
    """

    def test_create(self):
        """
        Test the create method
        """
        form = GeneralAssemblyFormFactory.create()

        self.assertEqual(type(form.schema), GeneralAssemblySchema)
        button_names = [button.name for button in form.buttons]
        self.assertTrue('submit' in button_names)
        self.assertTrue('reset' in button_names)
        self.assertTrue('cancel' in button_names)
        self.assertEqual(len(form.buttons), 3)
