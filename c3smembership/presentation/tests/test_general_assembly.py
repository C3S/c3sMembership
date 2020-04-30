# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.views.general_assembly module
"""
import datetime
import unittest

import mock
from pyramid import testing
from webob.multidict import MultiDict

import c3smembership.presentation.views.general_assembly as \
    general_assembly_module
from c3smembership.presentation.views.general_assembly import (
    general_assemblies,
    general_assembly_view,
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
        self.assertEqual(len(result['general_assemblies']), 2)

        # Verify decending order by number
        self.assertEqual(result['general_assemblies'][0].number, 2)
        self.assertEqual(result['general_assemblies'][1].number, 1)

    def test_general_assembly_view(self):
        """
        Test the general_assembly_view method
        """
        general_assembly = mock.Mock()
        general_assembly.number = 123
        general_assembly.name = 'my first general assembly'
        general_assembly.date = datetime.date(2018, 12, 15)
        general_assembly.invitation_subject_en = u'Assembly'
        general_assembly.invitation_text_en = u'Hello {salutation}!'
        general_assembly.invitation_subject_de = u'Versammlung'
        general_assembly.invitation_text_de = u'Hallo {salutation}!'
        request = testing.DummyRequest(
            validated_matchdict={'general_assembly': general_assembly})

        result = general_assembly_view(request)

        self.assertEqual(result['date'], datetime.date(2018, 12, 15))
        self.assertEqual(result['number'], 123)
        self.assertEqual(result['name'], 'my first general assembly')
        self.assertEqual(result['invitation_subject_en'], u'Assembly')
        self.assertEqual(result['invitation_text_en'], u'Hello {salutation}!')
        self.assertEqual(result['invitation_subject_de'], u'Versammlung')
        self.assertEqual(result['invitation_text_de'], u'Hallo {salutation}!')

    # pylint: disable=invalid-name
    @mock.patch.object(
        general_assembly_module, 'send_invitation')
    def test_general_assembly_invitation(self, send_invitation_mock):
        """
        Test the general_assembly_invitation method

        1. Setup
        2. Test members referer
        3. Test any other referer
        """
        # 1. Setup
        general_assembly = mock.Mock()
        general_assembly.number = 123
        member = mock.Mock()
        member.membership_number = 'membership_number'
        member.id = 789

        request = testing.DummyRequest(
            validated_matchdict={
                'general_assembly': general_assembly,
                'member': member,
            })

        test_config = testing.setUp(request=request)
        test_config.add_route('member_details', 'member_details')
        test_config.add_route('membership_listing_backend', '/memberships')

        # 2. Test members referer
        request.referer = '/members/'
        result = general_assembly_invitation(request)

        send_invitation_mock.assert_called_with(
            request, member, 123)
        self.assertEqual(result.status_code, 302)
        self.assertTrue('member_details#general-assembly' in result.location)

        # 3. Test any other referer
        request.referer = 'something'
        result = general_assembly_invitation(request)

        send_invitation_mock.assert_called_with(
            request, member, 123)
        self.assertEqual(result.status_code, 302)
        self.assertTrue('memberships#member_789' in result.location)

    @classmethod
    def _get_create_general_assembly_post(cls, assembly_name, assembly_date,
                                          invitation_subject_en,
                                          invitation_text_en,
                                          invitation_subject_de,
                                          invitation_text_de):
        POST = MultiDict()
        POST.add('__formid__', u'deform')
        POST.add('__start__', u'general_assembly:mapping')
        POST.add('name', assembly_name)
        POST.add('__start__', u'date:mapping')
        POST.add('date', unicode(assembly_date.strftime('%Y-%m-%d')))
        POST.add('__end__', u'date:mapping')
        POST.add('invitation_subject_en', invitation_subject_en)
        POST.add('invitation_text_en', invitation_text_en)
        POST.add('invitation_subject_de', invitation_subject_de)
        POST.add('invitation_text_de', invitation_text_de)
        POST.add('__end__', u'general_assembly:mapping')
        POST.add('submit', u'submit')
        return POST

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
        assembly_date = datetime.date.today() + datetime.timedelta(days=1)

        request = testing.DummyRequest(
            post=self._get_create_general_assembly_post(
                'New general assembly',
                assembly_date,
                u'Assembly',
                u'Hello {salutation}!',
                u'Versammlung',
                u'Hallo {salutation}!'))
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assemblies', 'general_assemblies')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .get_next_number.side_effect = [12345]

        result = general_assembly_create(request)

        self.assertEqual(result.status_code, 302)
        request.registry.general_assembly_invitation \
            .create_general_assembly.assert_called_with(
                u'New general assembly',
                assembly_date,
                u'Assembly',
                u'Hello {salutation}!',
                u'Versammlung',
                u'Hallo {salutation}!')
        testing.tearDown()

        # 3. Submit with date in the past
        assembly_date = datetime.date.today() - datetime.timedelta(days=1)
        request = testing.DummyRequest(
            post=self._get_create_general_assembly_post(
                'New general assembly',
                assembly_date,
                u'Assembly',
                u'Hello {salutation}!',
                u'Versammlung',
                u'Hallo {salutation}!'))
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
        4. Call for submit with validation failure
        """
        # Setup
        general_assembly = mock.Mock()
        general_assembly.number = 2398457932
        general_assembly.name = 'some assmembly'
        general_assembly.date = datetime.date(2019, 5, 11)

        # 1. Call for exiting general assembly
        request = testing.DummyRequest(
            validated_matchdict={'general_assembly': general_assembly})
        result = general_assembly_edit(request)

        self.assertTrue('2398457932' in result['form'])
        self.assertTrue('value="some assmembly"' in result['form'])
        self.assertTrue(
            'value="{0}"'.format(
                datetime.date(2019, 5, 11).strftime('%Y-%m-%d'))
            in
            result['form'])

        # 2. Call for cancel
        request = testing.DummyRequest(
            POST={'cancel': 'cancel'},
            validated_matchdict={'general_assembly': general_assembly})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')

        result = general_assembly_edit(request)

        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assembly')

        # 3. Call for submit
        general_assembly.number = 1
        request = testing.DummyRequest(
            post=self._get_create_general_assembly_post(
                'assembly name',
                datetime.date.today(),
                u'Assembly',
                u'Hello {salutation}!',
                u'Versammlung',
                u'Hallo {salutation}!'),
            validated_matchdict={'general_assembly': general_assembly})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        request.registry.general_assembly_invitation = mock.Mock()
        request.registry.general_assembly_invitation \
            .edit_general_assembly.side_effect = [None]
        result = general_assembly_edit(request)

        request.registry.general_assembly_invitation \
            .edit_general_assembly.assert_called_with(
                1, u'assembly name', datetime.date.today(),
                u'Assembly',
                u'Hello {salutation}!',
                u'Versammlung',
                u'Hallo {salutation}!')
        self.assertEqual(result.status_code, 302)
        self.assertEqual(
            result.location, 'http://example.com/general_assembly')

        # 4. Call for submit with validation failure
        request = testing.DummyRequest(
            POST={
                'submit': 'submit',
                'general_assembly': {
                    'date': (
                        datetime.date.today() - datetime.timedelta(days=1)
                    ).strftime('%Y-%m-%d'),
                    'name': 'assembly name'}},
            validated_matchdict={'general_assembly': general_assembly})
        test_config = testing.setUp(request=request)
        test_config.add_route('general_assembly', 'general_assembly')
        result = general_assembly_edit(request)

        self.assertTrue('form' in result)
        self.assertTrue('invalid-feedback' in result['form'])
