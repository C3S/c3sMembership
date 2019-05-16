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

from c3smembership.presentation.schemas.member import (
    MemberNode,
    MemberIdNode,
    MemberIdIsMemberNode,
)


class MemberNodeTestSchema(MappingSchema):
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
        schema = MemberNodeTestSchema()
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


class MemberIdNodeTestSchema(MappingSchema):
    """
    Dummy schema for testing the MemberIdNode class
    """
    member_id = MemberIdNode()


class TestMemberIdNode(TestCase):
    """
    Test the MemberIdNode class
    """

    def test_integration(self):
        """
        Integration test the MemberIdNode

        1. Success
        2. Failure, invalid number
        3. Failure, member not found
        """
        # 1. Success
        request = Mock()
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = ['some member']
        schema = MemberIdNodeTestSchema()
        data = schema \
            .bind(request=request) \
            .deserialize({'member_id': '123'})
        self.assertEqual(data['member_id'], 'some member')

        # 2. Failure, invalid number
        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'member_id': 'asdf'})

        self.assertEqual(
            invalid.exception.asdict()['member_id'],
            u'"asdf" is not a number')

        # 3. Failure, member not found
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = [None]

        with self.assertRaises(Invalid) as invalid:
            schema \
                .bind(request=request) \
                .deserialize({'member_id': '987'})

        self.assertEqual(
            invalid.exception.asdict()['member_id'],
            u'Member ID 987 does not exist.')

    def test_transform(self):
        """
        Test the transform method
        """
        request = Mock()
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = ['some member']
        node = MemberIdNode()
        result = node.transform(request, 'some value')

        self.assertEqual(result, 'some member')
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .assert_called_with('some value')


class MemberIdIsMemberNodeTestSchema(MappingSchema):
    """
    Dummy schema for testing the MemberIdNode class
    """
    member_id = MemberIdIsMemberNode()


class TestMemberIdIsMemberNode(TestCase):
    """
    Test the TestMemberIdIsMemberNode class
    """

    def test_integration(self):
        """
        Integration test the TestMemberIdIsMemberNode

        1. Validation success
        2. Validation failure
        3. No member found
        """
        # 1. Validation success
        member = Mock()
        member.is_member.side_effect = [True]
        request = Mock()
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = [member]
        schema = MemberIdIsMemberNodeTestSchema()

        data = schema \
            .bind(request=request) \
            .deserialize({'member_id': '123'})

        self.assertEqual(data['member_id'], member)

        # 2. Validation failure
        member.is_member.side_effect = [False]
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = [member]
        schema = MemberIdIsMemberNodeTestSchema()

        with self.assertRaises(Invalid) as invalid:
            data = schema \
                .bind(request=request) \
                .deserialize({'member_id': '123'})

        self.assertEqual(
            invalid.exception.asdict()['member_id'],
            u'Member with member ID 123 has not been granted membership')

        # 3. No member found
        request \
            .registry \
            .member_information \
            .get_member_by_id \
            .side_effect = [None]
        schema = MemberIdIsMemberNodeTestSchema()

        with self.assertRaises(Invalid) as invalid:
            data = schema \
                .bind(request=request) \
                .deserialize({'member_id': '123'})

        self.assertEqual(
            invalid.exception.asdict()['member_id'],
            u'Member ID 123 does not exist.')
