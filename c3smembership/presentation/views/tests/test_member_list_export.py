# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.views.member_list_export module
"""

import datetime
import unittest

from unittest import mock
from pyramid import testing
from webob.multidict import MultiDict

import c3smembership.presentation.views.member_list_export as \
    member_list_export_module
from c3smembership.presentation.views.member_list_export import (
    format_value,
    get_export_columns,
    get_filtered_members,
    get_member_rows,
    member_list_export_csv,
    member_list_export_print,
)


class MemberDummy(object):
    """
    Member dummy class holding the attributes to be exported
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        """
        Initialize the MemberDummy instance
        """
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestHelpers(unittest.TestCase):
    """
    Test the member list export helper functions
    """

    def test_format_value(self):
        """
        Test the format_value function
        """
        self.assertEqual(format_value(None), '')
        self.assertEqual(format_value(datetime.date(2026, 7, 3)), '2026-07-03')
        self.assertEqual(format_value(42), '42')
        self.assertEqual(format_value('Sömevälüe'), 'Sömevälüe')

    def test_get_export_columns(self):
        """
        Test the get_export_columns function

        The column order is defined by the export fields declaration and
        independent of the selection order.
        """
        columns = get_export_columns(set(['email', 'firstname']))
        self.assertEqual(
            [column[0] for column in columns],
            ['firstname', 'email'])

    def test_get_member_rows(self):
        """
        Test the get_member_rows function
        """
        member = MemberDummy(
            firstname='Anna',
            membership_loss_date=datetime.date(2026, 12, 31),
            membership_number=None)
        rows = get_member_rows(
            [member],
            [('firstname', 'First name'),
             ('membership_loss_date', 'Membership loss date'),
             ('membership_number', 'Membership number')])
        self.assertEqual(rows, [['Anna', '2026-12-31', '']])

    def test_get_filtered_members(self):
        """
        Test the get_filtered_members function

        1. Email exclusion pattern matching case-insensitively
        2. No email exclusion for an empty pattern
        3. Filter conversion of membership type and status
        """
        # 1. Email exclusion pattern matching case-insensitively
        anna = MemberDummy(email='anna@example.com')
        placeholder = MemberDummy(email='someone@member.INVALID')
        no_email = MemberDummy(email=None)
        request = mock.Mock()
        request.registry.member_information.get_members_filtered \
            .return_value = [anna, placeholder, no_email]

        members = get_filtered_members(request, {
            'fields': set(['email']),
            'email_exclude': '*.invalid',
            'membership_type': 'all',
            'membership_status': 'accepted',
            'membership_loss_date': datetime.date(2026, 7, 3),
        })

        self.assertEqual(members, [anna, no_email])
        request.registry.member_information.get_members_filtered \
            .assert_called_with(
                membership_type=None,
                membership_accepted=True,
                membership_loss_threshold=datetime.date(2026, 7, 3))

        # 2. No email exclusion for an empty pattern
        members = get_filtered_members(request, {
            'fields': set(['email']),
            'email_exclude': '',
            'membership_type': 'all',
            'membership_status': 'accepted',
            'membership_loss_date': datetime.date(2026, 7, 3),
        })

        self.assertEqual(members, [anna, placeholder, no_email])

        # 3. Filter conversion of membership type and status
        get_filtered_members(request, {
            'fields': set(['email']),
            'email_exclude': '',
            'membership_type': 'investing',
            'membership_status': 'all',
            'membership_loss_date': datetime.date(2026, 1, 1),
        })

        request.registry.member_information.get_members_filtered \
            .assert_called_with(
                membership_type='investing',
                membership_accepted=None,
                membership_loss_threshold=datetime.date(2026, 1, 1))


class TestMemberListExportViews(unittest.TestCase):
    """
    Test the member list export views
    """

    def setUp(self):
        self.request = testing.DummyRequest(post='')
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()

    @classmethod
    def _get_export_post(cls, fields, email_exclude, membership_type,
                         membership_status, membership_loss_date):
        """
        Build the deform POST data for the member list export form.
        """
        post = MultiDict()
        post.add('__formid__', 'deform')
        post.add('__start__', 'fields:sequence')
        for field in fields:
            post.add('checkbox', field)
        post.add('__end__', 'fields:sequence')
        post.add('email_exclude', email_exclude)
        post.add('membership_type', membership_type)
        post.add('membership_status', membership_status)
        post.add('__start__', 'membership_loss_date:mapping')
        post.add('date', membership_loss_date.strftime('%Y-%m-%d'))
        post.add('__end__', 'membership_loss_date:mapping')
        post.add('submit', 'submit')
        return post

    def test_csv_export_get(self):
        """
        Test the member_list_export_csv view rendering the form

        The email exclusion pattern defaults to "*.invalid" and the default
        fields are checked.
        """
        result = member_list_export_csv(self.request)

        self.assertTrue('value="*.invalid"' in result['form'])
        self.assertTrue('checked' in result['form'])

    def test_csv_export_post(self):
        """
        Test the member_list_export_csv view creating the CSV file

        The CSV file is semicolon separated with all values quoted, UTF-8
        encoded with a byte order mark and contains the technical field
        names as header row. The columns are ordered by the export fields
        declaration and members whose email address matches the exclusion
        pattern are excluded.
        """
        request = testing.DummyRequest(
            post=self._get_export_post(
                # selection order differs from export field order
                ['email', 'firstname'],
                '*.invalid',
                'all',
                'accepted',
                datetime.date(2026, 7, 3)))
        testing.setUp(request=request)
        request.registry.member_information = mock.Mock()
        request.registry.member_information.get_members_filtered \
            .return_value = [
                MemberDummy(firstname='Änna', email='anna@example.com'),
                MemberDummy(firstname='Bob', email='bob@member.invalid'),
            ]

        response = member_list_export_csv(request)

        self.assertEqual(response.content_type, 'text/csv')
        self.assertTrue(
            response.content_disposition.startswith('attachment;'))
        self.assertEqual(
            response.text,
            '\ufeff'
            '"firstname";"email"\r\n'
            '"Änna";"anna@example.com"\r\n')
        request.registry.member_information.get_members_filtered \
            .assert_called_with(
                membership_type=None,
                membership_accepted=True,
                membership_loss_threshold=datetime.date(2026, 7, 3))

    def test_csv_export_validation_failure(self):
        """
        Test the member_list_export_csv view with invalid form data

        Without any field selected the form validation fails and the form
        is shown again.
        """
        post = MultiDict()
        post.add('__formid__', 'deform')
        post.add('email_exclude', '*.invalid')
        post.add('membership_type', 'all')
        post.add('membership_status', 'accepted')
        post.add('__start__', 'membership_loss_date:mapping')
        post.add('date', '2026-07-03')
        post.add('__end__', 'membership_loss_date:mapping')
        post.add('submit', 'submit')
        request = testing.DummyRequest(post=post)
        testing.setUp(request=request)

        result = member_list_export_csv(request)

        self.assertTrue('form' in result)

    def test_print_get(self):
        """
        Test the member_list_export_print view rendering the form

        The email exclusion pattern defaults to an empty string so that no
        member is excluded from the print list by default.
        """
        result = member_list_export_print(self.request)

        self.assertTrue('value="*.invalid"' not in result['form'])
        self.assertTrue('Show print list' in result['form'])

    @mock.patch.object(member_list_export_module, 'render_to_response')
    def test_print_post(self, render_to_response_mock):
        """
        Test the member_list_export_print view rendering the print list
        """
        render_to_response_mock.side_effect = ['rendered']
        request = testing.DummyRequest(
            post=self._get_export_post(
                ['firstname', 'lastname'],
                '',
                'normal',
                'accepted',
                datetime.date(2026, 7, 3)))
        testing.setUp(request=request)
        request.registry.member_information = mock.Mock()
        request.registry.member_information.get_members_filtered \
            .return_value = [
                MemberDummy(firstname='Änna', lastname='Ählgren'),
            ]

        result = member_list_export_print(request)

        self.assertEqual(result, 'rendered')
        values = render_to_response_mock.call_args[0][1]
        self.assertEqual(values['count'], 1)
        self.assertEqual(values['rows'], [['Änna', 'Ählgren']])
        self.assertEqual(
            values['membership_loss_date'], datetime.date(2026, 7, 3))
        self.assertEqual(
            [str(title) for title in values['column_titles']],
            ['First name', 'Last name'])
        request.registry.member_information.get_members_filtered \
            .assert_called_with(
                membership_type='normal',
                membership_accepted=True,
                membership_loss_threshold=datetime.date(2026, 7, 3))
