# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.schemas.member module
"""

from unittest import TestCase

from colander import (
    Invalid,
    MappingSchema,
)
from mock import Mock

from c3smembership.presentation.schemas.member import MemberNode


class DummySchema(MappingSchema):
    """
    Dummy schema for testing the MemberNode class
    """
    membership_number = MemberNode()


class TestMemberNode(TestCase):
    """
    Test the MemberNode class
    """

    def test_integration(self):
        """
        Integration test the MemberNode

        1. Success
        2. Failure, invalid number
        3. Failure, member not found
        """
        # 1. Success
        request = Mock()
        request \
            .registry \
            .member_information \
            .get_member \
            .side_effect = ['some member']
        schema = DummySchema()
        data = schema \
            .bind(request=request) \
            .deserialize({'membership_number': '123'})
        self.assertEqual(data['membership_number'], 'some member')

        # 2. Failure, invalid number
        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'membership_number': 'asdf'})

        self.assertEqual(
            invalid.exception.asdict()['membership_number'],
            u'"asdf" is not a number')

        # 3. Failure, member not found
        request \
            .registry \
            .member_information \
            .get_member \
            .side_effect = [None]

        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'membership_number': '987'})

        self.assertEqual(
            invalid.exception.asdict()['membership_number'],
            u'Membership number 987 does not exist.')

    def test_transform(self):
        """
        Test the transform method
        """
        request = Mock()
        request \
            .registry \
            .member_information \
            .get_member \
            .side_effect = ['some member']
        node = MemberNode()
        result = node.transform(request, 'some value')

        self.assertEqual(result, 'some member')
        request \
            .registry \
            .member_information \
            .get_member \
            .assert_called_with('some value')
