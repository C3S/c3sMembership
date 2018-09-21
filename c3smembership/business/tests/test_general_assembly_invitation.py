# -*- coding: utf-8 -*-
"""
Test the c3smembership.business.general_assembly_invitation module
"""

from datetime import date
from unittest import TestCase

import mock

from c3smembership.business.general_assembly_invitation import \
    GeneralAssemblyInvitation


class GeneralAssemblyInvitationTest(TestCase):
    """
    Test the GeneralAssemblyInvitation class
    """

    def test_get_member_invitations(self):
        """
        Test the get_member_invitations method
        """
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

    def test_invite_member(self):
        """
        Test the invite_member method

        1. Test general assembly in the past
        2. Test invite member not eligible
        3. Test member already invited
        4. Test member invitation
        """
        general_assembly = mock.Mock()
        general_assembly.date = date(2018, 9, 15)
        general_assembly.number = 'GA1'
        date_dummy = mock.Mock()
        member = mock.Mock()
        member.membership_number = 'M1'
        token = 'ABCDE'

        general_assembly_repository = mock.Mock()
        gai = GeneralAssemblyInvitation(general_assembly_repository)

        # 1. Test general assembly in the past
        date_dummy.today.side_effect = [date(2018, 9, 16)]
        gai.date = date_dummy

        with self.assertRaises(ValueError) as raise_context:
            gai.invite_member(None, general_assembly, None)
        self.assertEqual(
            str(raise_context.exception),
            'The general assembly occurred in the past.')

        # 2. Test invite member not eligible
        date_dummy.today.side_effect = [date(2018, 9, 15)]
        member.is_member.side_effect = [False]

        with self.assertRaises(ValueError) as raise_context:
            gai.invite_member(member, general_assembly, None)
        member.is_member.assert_called_with(date(2018, 9, 15))
        self.assertEqual(
            str(raise_context.exception),
            'The member is not eligible to be invited to the general assembly')

        # 3. Test member already invited
        date_dummy.today.side_effect = [date(2018, 9, 15)]
        member.is_member.side_effect = [True]
        general_assembly_repository.get_member_invitation.side_effect = [
            {'flag': True}]

        with self.assertRaises(ValueError) as raise_context:
            gai.invite_member(member, general_assembly, None)
        member.is_member.assert_called_with(date(2018, 9, 15))
        general_assembly_repository.get_member_invitation.assert_called_with(
            'M1', 'GA1')
        self.assertEqual(
            str(raise_context.exception),
            'The member has already been invited to the general assembly.')

        # 4. Test member invitation
        date_dummy.today.side_effect = [date(2018, 9, 15)]
        member.is_member.side_effect = [True]
        general_assembly_repository.get_member_invitation.side_effect = [None]

        gai.invite_member(member, general_assembly, token)
        member.is_member.assert_called_with(date(2018, 9, 15))
        general_assembly_repository.get_member_invitation.assert_called_with(
            'M1', 'GA1')
        general_assembly_repository.invite_member.assert_called_with(
            'M1', 'GA1', token)
