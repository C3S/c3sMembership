# -*- coding: utf-8 -*-

from datetime import date

from unittest import TestCase, mock

from c3smembership.business.member_information import (
    MemberInformation,
)


class MemberInformationTest(TestCase):

    def test_get_accepted_members_count(self):
        member_repository_mock = mock.Mock()
        member_repository_mock.get_accepted_members_count.side_effect = [
            'get_accepted_members_count result']

        member_information = MemberInformation(member_repository_mock)
        effective_date = date(2017, 8, 24)

        accepted_members_count = member_information.get_accepted_members_count(
            effective_date)

        member_repository_mock.get_accepted_members_count.assert_called_with(
            effective_date)
        self.assertEqual(
            accepted_members_count,
            'get_accepted_members_count result')

    def test_get_accepted_members_sorted(self):
        member_repository_mock = mock.Mock()
        member_repository_mock.get_accepted_members_sorted.side_effect = [
            'get_accepted_members_sorted result']

        member_information = MemberInformation(member_repository_mock)
        effective_date = date(2017, 8, 24)

        accepted_members_sorted = member_information.get_accepted_members_sorted(
            effective_date)

        member_repository_mock.get_accepted_members_sorted.assert_called_with(
            effective_date)
        self.assertEqual(
            accepted_members_sorted,
            'get_accepted_members_sorted result')

    def test_get_member(self):
        member_repository_mock = mock.Mock()
        member_repository_mock.get_member.side_effect = [
            'get_member result']

        member_information = MemberInformation(member_repository_mock)

        member = member_information.get_member('1234')

        member_repository_mock.get_member.assert_called_with('1234')
        self.assertEqual(
            member,
            'get_member result')
