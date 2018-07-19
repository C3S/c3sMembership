# -*- coding: utf-8 -*-

import unittest
from pyramid import testing

from c3smembership.presentation.views.membership_member_get import get_member


class MemberInformationDummy(object):

    def __init__(self, result):
        self.__result = result

    def get_member_by_id(self, member_id):
        self.member_id = member_id
        return self.__result


class MemberDummy(object):

    def __init__(self, id, firstname, lastname):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname


class TestGetMember(unittest.TestCase):

    def test_get_member(self):
        # test member found
        member_information = MemberInformationDummy(
            MemberDummy(321, 'Shannon', 'Jones'))
        request_dummy = testing.DummyRequest(matchdict={'member_id': 123})
        request_dummy.registry.member_information = member_information
        request_dummy.matchdict = {'member_id': 123}
        result = get_member(request_dummy)

        self.assertEqual(member_information.member_id, 123)
        self.assertEqual(result['id'], 321)
        self.assertEqual(result['firstname'], 'Shannon')
        self.assertEqual(result['lastname'], 'Jones')

        # test member not found
        member_information = MemberInformationDummy(None)
        request_dummy = testing.DummyRequest(matchdict={'member_id': 123})
        request_dummy.registry.member_information = member_information
        request_dummy.matchdict = {'member_id': 123}
        result = get_member(request_dummy)

        self.assertEqual(member_information.member_id, 123)
        self.assertEqual(result, {})
