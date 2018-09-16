# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.templates.pages.membership_member_detail
template.
"""

from datetime import (
    date,
    datetime,
)
import unittest

from pyramid import renderers
from pyramid.testing import DummyRequest
import pyramid.testing


class DateDummy(object):

    def __init__(self, today):
        self.__today = today

    def today(self):
        return self.__today


class DummyMember(object):

    def __init__(self, id):
        self.id = id


class TestMembershipMemberDetail(unittest.TestCase):

    def setUp(self):
        self.config = pyramid.testing.setUp()
        self.config.include('pyramid_chameleon')
        self.config.add_route('invite_member', 'invite_member/{m_id}')

    @classmethod
    def render(cls, values):
        """
        Render the values and return the rendered HTML.
        """
        request = DummyRequest()
        return renderers.render(
            (
                '../templates/page-elements/'
                'membership_member_detail_general_assembly.pt'
            ),
            values,
            request)

    def test_no_general_assemblies(self):
        """
        Test displaying no general assemblies.
        """
        html = self.render(
            {
                'general_assembly_invitations': [],
            })
        self.assertTrue(
            'There are no general assemblies relevant for this member.' \
            in html)

    def test_general_assemblies(self):
        """
        Test displaying general assemblies

        Test cases:

        1. Show invitation link when indicated
        2. Do not show invitation link when not indicated
        3. Show sent timestamp
        4. Show multiple assemblies
        """
        # 1. Show invitation link when assembly later than today
        html = self.render(
            {
                'general_assembly_invitations': [
                    {
                        'number': 'GA1',
                        'name': 'assembly one',
                        'date': date(2018, 9, 16),
                        'flag': False,
                        'sent': None,
                        'can_invite': True,
                    },
                ],
                'member': DummyMember(1234),
            })
        self.assertTrue('GA1' in html)
        self.assertTrue('assembly one' in html)
        self.assertTrue('16.09.2018' in html)
        self.assertTrue('text-warning' in html)
        self.assertTrue('href="http://example.com/invite_member/1234"' in html)

        # 2. Do not show invitation link when assembly earlier than today
        html = self.render(
            {
                'general_assembly_invitations': [
                    {
                        'number': 'GA1',
                        'name': 'assembly one',
                        'date': date(2018, 9, 16),
                        'flag': False,
                        'sent': None,
                        'can_invite': False,
                    },
                ],
                'member': DummyMember(1234),
            })
        self.assertTrue('GA1' in html)
        self.assertTrue('assembly one' in html)
        self.assertTrue('16.09.2018' in html)
        self.assertTrue('text-danger' in html)
        self.assertTrue(
            'href="http://example.com/invite_member/1234"' not in html)

        # 3. Show sent timestamp
        html = self.render(
            {
                'general_assembly_invitations': [
                    {
                        'number': 'GA1',
                        'name': 'assembly one',
                        'date': date(2018, 9, 16),
                        'flag': True,
                        'sent': datetime(2018, 9, 14, 10, 11, 12),
                        'can_invite': False,
                    },
                ],
                'member': DummyMember(1234),
            })
        self.assertTrue('GA1' in html)
        self.assertTrue('assembly one' in html)
        self.assertTrue('16.09.2018' in html)
        self.assertTrue('text-success' in html)
        self.assertTrue('14.09.2018 10:11:12' in html)
        self.assertTrue(
            'href="http://example.com/invite_member/1234"' not in html)

        # 4. Show multiple assemblies
        html = self.render(
            {
                'general_assembly_invitations': [
                    {
                        'number': 'GA2',
                        'name': 'assembly two',
                        'date': date(2019, 1, 11),
                        'flag': False,
                        'sent': None,
                        'can_invite': True,
                    },
                    {
                        'number': 'GA1',
                        'name': 'assembly one',
                        'date': date(2018, 9, 16),
                        'flag': True,
                        'sent': datetime(2018, 9, 14, 10, 11, 12),
                        'can_invite': False,
                    },
                ],
                'member': DummyMember(1234),
            })
        self.assertTrue('GA2' in html)
        self.assertTrue('assembly two' in html)
        self.assertTrue('11.01.2019' in html)
        self.assertTrue('text-warning' in html)
        self.assertTrue('href="http://example.com/invite_member/1234"' in html)

        self.assertTrue('GA1' in html)
        self.assertTrue('assembly one' in html)
        self.assertTrue('16.09.2018' in html)
        self.assertTrue('text-success' in html)
        self.assertTrue('14.09.2018 10:11:12' in html)
