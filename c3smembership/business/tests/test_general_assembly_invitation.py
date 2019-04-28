# -*- coding: utf-8 -*-
"""
Test the c3smembership.business.general_assembly_invitation module
"""

from datetime import date
from unittest import TestCase

import mock

from c3smembership.business.general_assembly_invitation import \
    GeneralAssemblyInvitation
from c3smembership.data.model.base.general_assembly import GeneralAssembly


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

    def test_get_member_invitation(self):
        """
        Test the get_member_invitation method

        Verify that it returns the general assembly with the correct number
        from the list it got from the get_member_invitations method.
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
            # First method call
            [
                # In the past and not invited => no invitation
                {
                    'flag': False,
                    'date': date(2018, 9, 15),
                    'number': 1,
                },
                # In the past and invited => no invitation
                {
                    'flag': True,
                    'date': date(2018, 9, 15),
                    'number': 2,
                },
            ],
            # Second method call
            [
                # In the past and not invited => no invitation
                {
                    'flag': False,
                    'date': date(2018, 9, 15),
                    'number': 1,
                },
                # In the past and invited => no invitation
                {
                    'flag': True,
                    'date': date(2018, 9, 15),
                    'number': 2,
                },
            ],
        ]

        gai = GeneralAssemblyInvitation(general_assembly_repository)
        gai.date = date_dummy
        invitation = gai.get_member_invitation(member, 1)
        self.assertEqual(invitation['number'], 1)
        invitation = gai.get_member_invitation(member, 2)
        self.assertEqual(invitation['number'], 2)

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

    def test_get_general_assembly(self):
        """
        Test the get_general_assembly method
        """
        general_assembly_repository = mock.Mock()
        general_assembly_repository.get_general_assembly.side_effect = [
            'get_general_assembly result']
        gai = GeneralAssemblyInvitation(general_assembly_repository)
        result = gai.get_general_assembly(123)
        self.assertEqual(result, 'get_general_assembly result')
        general_assembly_repository.get_general_assembly.assert_called_with(
            123)

    def test_get_general_assemblies(self):
        """
        Test the get_general_assemblies method
        """
        general_assembly_repository = mock.Mock()
        general_assembly_repository.get_general_assemblies.side_effect = [
            'get_general_assemblies result']
        gai = GeneralAssemblyInvitation(general_assembly_repository)
        result = gai.get_general_assemblies()
        self.assertEqual(result, 'get_general_assemblies result')

    def test_create_general_assembly(self):
        """
        Test the create_general_assembly method

        1. Create a general assembly in the future and verify the calls
        2. Create a general assembly for today
        3. Try creating a general assembly in the past
        """
        general_assembly_repository = mock.Mock()
        gai = GeneralAssemblyInvitation(general_assembly_repository)
        gai.date = mock.Mock()

        # 1. Create a general assembly in the future and verify the calls
        general_assembly_repository.general_assembly_max_number.side_effect = [
            10]
        gai.date.today.side_effect = [date(2018, 11, 17)]

        gai.create_general_assembly(
            u'New general assembly', date(2018, 11, 18))

        gai.date.today.assert_called_with()
        general_assembly_repository.general_assembly_max_number \
            .assert_called_with()
        general_assembly_repository.create_general_assembly.assert_called_with(
            11, u'New general assembly', date(2018, 11, 18))

        # 2. Create a general assembly for today
        general_assembly_repository.general_assembly_max_number.side_effect = [
            21]
        gai.date.today.side_effect = [date(2018, 11, 20)]

        gai.create_general_assembly(
            u'Another general assembly', date(2018, 11, 20))

        gai.date.today.assert_called_with()
        general_assembly_repository.general_assembly_max_number \
            .assert_called_with()
        general_assembly_repository.create_general_assembly.assert_called_with(
            22, u'Another general assembly', date(2018, 11, 20))

        # 3. Try creating a general assembly in the past
        gai.date.today.side_effect = [date(2018, 11, 19)]
        with self.assertRaises(ValueError) as raise_context:
            gai.create_general_assembly(
                u'New general assembly', date(2018, 11, 18))
        self.assertEqual(
            str(raise_context.exception),
            'The general assembly must take place in the future.')

    def test_edit_general_assembly(self):
        """
        Test the edit_general_assembly method

        1. Edit a general assembly in the future and verify the calls
        2. Edit a general assembly for today
        3. Try editing a general assembly in the past
        4. Try editing a general assembly that does not exist
        """
        general_assembly_repository = mock.Mock()
        gai = GeneralAssemblyInvitation(general_assembly_repository)
        gai.date = mock.Mock()

        # 1. Edit a general assembly in the future and verify the calls
        general_assembly_repository.get_general_assembly.side_effect = [
            GeneralAssembly(1, 'Old general assembly name', date(2019, 1, 22))]
        gai.date.today.side_effect = [date(2019, 1, 21)]
        gai.edit_general_assembly(
            1, u'New general assembly name', date(2019, 1, 23))

        gai.date.today.assert_called_with()
        general_assembly_repository.edit_general_assembly.assert_called_with(
            1, u'New general assembly name', date(2019, 1, 23))

        # 2. Edit a general assembly for today
        general_assembly_repository.get_general_assembly.side_effect = [
            GeneralAssembly(1, 'Old general assembly name', date(2019, 1, 22))]
        gai.date.today.side_effect = [date(2019, 1, 21)]
        gai.edit_general_assembly(
            1, u'New general assembly name', date(2019, 1, 21))

        gai.date.today.assert_called_with()
        general_assembly_repository.edit_general_assembly.assert_called_with(
            1, u'New general assembly name', date(2019, 1, 21))

        # 3. Try editing a general assembly in the past
        gai.date.today.side_effect = [date(2019, 1, 21)]
        with self.assertRaises(ValueError) as raise_context:
            gai.edit_general_assembly(
                1, u'New general assembly name', date(2019, 1, 20))
        self.assertEqual(
            str(raise_context.exception),
            'The general assembly must take place in the future.')

        # 4. Try editing a general assembly that does not exist
        general_assembly_repository.get_general_assembly.side_effect = [None]
        gai.date.today.side_effect = [date(2019, 1, 21)]

        with self.assertRaises(ValueError) as raise_context:
            gai.edit_general_assembly(
                1, u'New general assembly name', date(2019, 1, 22))
        self.assertEqual(
            str(raise_context.exception),
            'The general assembly does not exist.')

    def test_get_latest_general_assembly(self):
        """
        Test the get_latest_general_assembly method

        Verified that it passed the call on to the repository.
        """
        general_assembly_repository = mock.Mock()
        general_assembly_repository.get_latest_general_assembly.side_effect = [
            'latest general assembly']

        gai = GeneralAssemblyInvitation(general_assembly_repository)
        latest_general_assembly = gai.get_latest_general_assembly()
        self.assertEqual(latest_general_assembly, 'latest general assembly')
        general_assembly_repository.get_latest_general_assembly \
            .assert_called_with()
