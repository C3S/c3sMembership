# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.views.general_assembly module
"""
import datetime
import unittest

import mock
from pyramid import testing

import c3smembership.presentation.views.general_assembly as \
    general_assembly_module
from c3smembership.presentation.views.general_assembly import (
    general_assemblies,
    general_assembly,
    general_assembly_invitation,
    general_assembly_create,
    general_assembly_edit,
)


class GeneralAssemblyDummy(object):
    """
    General assembly dummy class
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, number, name, date):
        """
        Initialize the GeneralAssemblyDummy instance
        """
        self.number = number
        self.name = name
        self.date = date


class TestGeneralAssembly(unittest.TestCase):
    """
    Test the general assembly module
    """

    def test_general_assemblies(self):
        """
        Test the general_assemblies method
        """
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

    def test_general_assembly(self):
        """
        Test the general assembly method

        1. No number given
        2. Return general assembly
        """
        # 1. No number given
        request = testing.DummyRequest()
        result = general_assembly(request)
        self.assertIsNone(result['date'])
        self.assertIsNone(result['number'])
        self.assertIsNone(result['name'])

        # 2. Return general assembly
        request = testing.DummyRequest(matchdict={'number': '1'})
        result_mock = mock.Mock()
        result_mock.number = 123
        result_mock.name = 'my first general assembly'
        result_mock.date = datetime.date(2018, 12, 15)
        gai = mock.Mock()
        gai.get_general_assembly.side_effect = [result_mock]
        request.registry.general_assembly_invitation = gai
        result = general_assembly(request)
        self.assertEquals(result['date'], datetime.date(2018, 12, 15))
        self.assertEquals(result['number'], 123)
        self.assertEquals(result['name'], 'my first general assembly')

    # pylint: disable=invalid-name
    @mock.patch.object(
        general_assembly_module, 'send_invitation')
    def test_general_assembly_invitation(self, send_invitation_mock):
        """
        Test the general_assembly_invitation method

        1. Invite
        2. Invalid general assembly number
        3. Invalid membership number
        4. Member not found
        """
        # 1. Invite
        member_information = mock.Mock()
        member = mock.Mock()
        member.membership_number.side_effect = ['membership_number']
        member_information.get_member.side_effect = [member]

        # request = mock.Mock()
        # request.registry.member_information = member_information
        # request.matchdict.get.side_effect = [
        #     '1',  # general assembly
        #     '2',  # member
        # ]
        # general_assembly_invitation(request)
        request = testing.DummyRequest(matchdict={
            'number': '1',
            'membership_number': '2',
        })
        request.referer = 'something'
        test_config = testing.setUp(request=request)
        test_config.add_route('member_details', 'member_details')
        test_config.add_route('membership_listing_backend', '/memberships')
        request.registry.member_information = member_information
        general_assembly_invitation(request)

        # In order to send an invitation the method has to
        # i. get the member for the membership_number converted to an integer
        member_information.get_member.assert_called_with(2)
        # ii. call the send_invitation method passing, request, member and
        #      general assembly number
        send_invitation_mock.assert_called_with(
            request, member, 1)

        # 2. Invalid general assembly number
        request = testing.DummyRequest(matchdict={
            'number': 'a',
        })
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')
        result = general_assembly_invitation(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            request.session.pop_flash('message_to_staff')[0],
            'Invalid general assembly number')

        # 3. Invalid membership number
        request = testing.DummyRequest(matchdict={
            'number': '1',
            'membership_number': 'a',
        })
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        result = general_assembly_invitation(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            request.session.pop_flash('message_to_staff')[0],
            'Invalid membership number')

        # 4. Member not found
        request = testing.DummyRequest(matchdict={
            'number': '1',
            'membership_number': '1',
        })
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        request.registry.member_information = mock.Mock()
        request.registry.member_information.get_member.side_effect = [None]
        result = general_assembly_invitation(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            request.session.pop_flash('message_to_staff')[0],
            'Invalid membership number')

    def test_general_assembly_create(self):
        """
        Test the general_assembly_create method

        1. Call to render the empty form
        2. Submit without error
        3. Submit with date in the past
        4. Submit without assembly name
        """
        # 1. Call to render the empty form
        request = testing.DummyRequest(post='')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_next_number.side_effect = [12345]
        result = general_assembly_create(request)
        self.assertTrue('12345' in result['form'])

        # 2. Submit without error
        test_config = testing.setUp()
        test_config.add_route('general_assemblies', 'general_assemblies')
        assembly_date = datetime.date.today() + datetime.timedelta(days=1)
        request = testing.DummyRequest(post={
            'submit': 'submit',
            'general_assembly': {
                'name': u'New general assembly',
                'date': assembly_date.strftime('%Y-%m-%d')}})
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_next_number.side_effect = [12345]

        result = general_assembly_create(request)

        self.assertEqual(result.status_code, 302)
        request.registry.general_assembly_invitation \
            .create_general_assembly.assert_called_with(
                u'New general assembly',
                assembly_date)
        testing.tearDown()

        # 3. Submit with date in the past
        assembly_date = datetime.date.today() - datetime.timedelta(days=1)
        request = testing.DummyRequest(post={
            'submit': 'submit',
            'general_assembly': {
                'name': u'New general assembly',
                'date': assembly_date.strftime('%Y-%m-%d')}})
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_next_number.side_effect = [12345]
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')

        result = general_assembly_create(request)

        self.assertTrue(
            'There was a problem with your submission' in result['form'])
        self.assertTrue(
            'is in the past. The general assembly must take place in the '
            'future.' in result['form'])
        testing.tearDown()

        # 4. Submit without assembly name
        assembly_date = datetime.date.today() + datetime.timedelta(days=1)
        request = testing.DummyRequest(post={
            'submit': 'submit',
            'general_assembly': {
                'name': u'',
                'date': assembly_date.strftime('%Y-%m-%d')}})
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_next_number.side_effect = [12345]
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')

        result = general_assembly_create(request)

        self.assertTrue(
            'There was a problem with your submission' in result['form'])
        testing.tearDown()

    def test_general_assembly_edit(self):
        """
        Test the general_assembly_create method

        1. Call for exiting general assembly
        2. Call for cancel
        3. Call for submit
        4. Call for non-exiting general assembly
        5. Call for submit with validation failure
        6. Call for invalid general assembly nunmber
        """
        # 1. Call for exiting general assembly
        request = testing.DummyRequest(matchdict={'number': '2398457932'})
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_general_assembly.side_effect = [
                GeneralAssemblyDummy(
                    2398457932,
                    'some assmembly',
                    datetime.date.today())]
        result = general_assembly_edit(request)

        request.registry.general_assembly_invitation \
            .get_general_assembly.assert_called_with(2398457932)
        self.assertTrue('2398457932' in result['form'])
        self.assertTrue('value="some assmembly"' in result['form'])
        self.assertTrue(
            'value="{0}"'.format(
                datetime.date.today().strftime('%Y-%m-%d'))
            in
            result['form'])

        # 2. Call for cancel
        request = testing.DummyRequest(
            matchdict={'number': '1'},
            POST={'cancel': 'cancel'})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        result = general_assembly_edit(request)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assembly')

        # 3. Call for submit
        request = testing.DummyRequest(
            matchdict={'number': '1'},
            POST={
                'submit': 'submit',
                'general_assembly': {
                    'date': datetime.date.today().strftime('%Y-%m-%d'),
                    'name': 'assembly name'}})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .edit_general_assembly.side_effect = [None]
        result = general_assembly_edit(request)

        request.registry.general_assembly_invitation \
            .edit_general_assembly.assert_called_with(
                1, u'assembly name', datetime.date.today())
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assembly')

        # 4. Call for non-exiting general assembly
        request = testing.DummyRequest(matchdict={'number': '2398457932'})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_general_assembly.side_effect = [None]
        result = general_assembly_edit(request)

        request.registry.general_assembly_invitation \
            .get_general_assembly.assert_called_with(2398457932)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assemblies')

        # 5. Call for submit with validation failure
        request = testing.DummyRequest(
            matchdict={'number': '1'},
            POST={
                'submit': 'submit',
                'general_assembly': {
                    'date': (
                        datetime.date.today() - datetime.timedelta(days=1)
                    ).strftime('%Y-%m-%d'),
                    'name': 'assembly name'}})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .edit_general_assembly.side_effect = [None]
        result = general_assembly_edit(request)

        self.assertTrue('form' in result)
        self.assertTrue('invalid-feedback' in result['form'])

        # 6. Call for invalid general assembly nunmber
        request = testing.DummyRequest(matchdict={'number': 'NaN'})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')
        result = general_assembly_edit(request)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assemblies')
