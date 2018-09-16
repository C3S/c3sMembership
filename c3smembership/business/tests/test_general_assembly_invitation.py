# -*- coding: utf-8 -*-

from datetime import date
import mock
from unittest import TestCase

from c3smembership.business.general_assembly_invitation import \
    GeneralAssemblyInvitation


class DateDummy(object):

    def __init__(self, today):
        self._today = today

    def today(self):
        return self._today


class MemberDummy(object):

    def __init__(
            self, membership_number, membership_date, membership_loss_date):
        self.membership_number = membership_number
        self.membership_date = membership_date
        self.membership_loss_date = membership_loss_date


class GeneralAssemblyInvitationTest(TestCase):

    def test_get_member_invitations(self):
        date_dummy = mock.Mock()
        date_dummy.today.side_effect = [
            date(2018, 9, 16),
            date(2018, 9, 16),
            date(2018, 9, 16),
            date(2018, 9, 16),
        ]

        member = mock.Mock()
        member.membership_number = 'membership number'
        member.membership_date = 'membership date'
        member.membership_loss_date = 'membership loss date'

        general_assembly_repository = mock.Mock()
        general_assembly_repository.get_member_invitations.side_effect = [
            [
                # In the past and not invited => no invitation
                {
                    'flag': False,
                    'date': date(2018, 9, 15),
                },
                # In the past and invited => no invitation
                {
                    'flag': True,
                    'date': date(2018, 9, 15),
                },
                # In the future and not invited => invitation
                {
                    'flag': False,
                    'date': date(2018, 9, 17),
                },
                # In the future and invited => no invitation
                {
                    'flag': True,
                    'date': date(2019, 1, 1),
                },
            ]]

        gai = GeneralAssemblyInvitation(general_assembly_repository)
        gai.date = date_dummy
        invitations = gai.get_member_invitations(member)
        self.assertEqual(invitations[0]['can_invite'], False)
        self.assertEqual(invitations[1]['can_invite'], False)
        self.assertEqual(invitations[2]['can_invite'], True)
        self.assertEqual(invitations[3]['can_invite'], False)
