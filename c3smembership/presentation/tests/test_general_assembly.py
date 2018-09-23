# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.views.general_assembly module
"""

import unittest

import mock

import c3smembership.presentation.views.general_assembly as \
    general_assembly_module
from c3smembership.presentation.views.general_assembly import (
    general_assemblies,
    general_assembly_invitation,
)


class TestGeneralAssembly(unittest.TestCase):
    """
    Test the general assembly module
    """

    def test_general_assemblies(self):
        request = mock.Mock()
        ga1 = mock.Mock()
        ga1.number = 1
        ga2 = mock.Mock()
        ga2.number = 2
        request.registry.general_assembly_invitation \
            .get_general_assemblies.side_effect = [[ga1, ga2]]
        result = general_assemblies(request)

        # Verify assemblies count
        self.assertEquals(len(result['general_assemblies']), 2)

        # Verify decending order by number
        self.assertEquals(result['general_assemblies'][0].number, 2)
        self.assertEquals(result['general_assemblies'][1].number, 1)

    # pylint: disable=invalid-name
    @mock.patch.object(
        general_assembly_module, 'send_invitation')
    def test_general_assembly_invitation(self, send_invitation_mock):
        """
        Test the general_assembly_invitation method
        """
        # pylint: disable=no-self-use
        member_information = mock.Mock()
        member_information.get_member.side_effect = [
            'member']

        request = mock.Mock()
        request.registry.member_information = member_information
        request.matchdict.get.side_effect = [
            '1',  # general assembly
            '2',  # member
        ]

        general_assembly_invitation(request)

        # In order to send an invitation the method has to
        # 1. get the general assembly number and membership_number from the
        #    matchdict
        request.matchdict.get.assert_has_calls([
            mock.call('number'),
            mock.call('membership_number'),
        ])
        # 2. get the member for the membership_number converted to an integer
        member_information.get_member.assert_called_with(2)
        # 3. call the send_invitation method passing, request, member and
        #    general assembly number
        send_invitation_mock.assert_called_with(
            request, 'member', 1)
