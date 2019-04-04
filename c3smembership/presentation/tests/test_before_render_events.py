# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.before_render_events module
"""

import unittest

import mock

from c3smembership.presentation import before_render_events
from c3smembership.presentation.before_render_events import \
    version_before_render


class TestVersionBeforeRender(unittest.TestCase):
    """
    Test the version_before_render method
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, methodName='runTest'):
        super(TestVersionBeforeRender, self).__init__(methodName)
        self._read_mock = None

    def setUp(self):
        # TODO: This is dependency injection to dirty way and needs to be clean
        # up
        self._os_mock = mock.Mock()
        self._git_tools_mock = mock.Mock()
        self._open_mock = mock.Mock()
        self._excluded_routes = []

        self._original_os = before_render_events.os
        self._original_git_tools = before_render_events.GitTools
        self._original_excluded_routes = before_render_events.EXCLUDED_ROUTES

        before_render_events.os = self._os_mock
        before_render_events.open = self._open_mock
        before_render_events.GitTools = self._git_tools_mock
        before_render_events.EXCLUDED_ROUTES = self._excluded_routes

    def tearDown(self):
        before_render_events.os = self._original_os
        before_render_events.GitTools = self._original_git_tools
        before_render_events.EXCLUDED_ROUTES = self._original_excluded_routes
        before_render_events.open = open

    def _set_version_read(self, version):
        self._read_mock = mock.Mock()
        self._read_mock.read.side_effect = [version]
        self._open_mock.side_effect = [self._read_mock]

    def _set_git_tag(self, tag):
        self._git_tools_mock.get_tag.side_effect = [tag]

    def _set_git_branch(self, branch):
        self._git_tools_mock.get_branch.side_effect = [branch]

    def _set_git_get_commit_hash(self, commit_hash):
        self._git_tools_mock.get_commit_hash.side_effect = [commit_hash]

    def _set_git_get_github_commit_url(self, github_commit_url):
        self._git_tools_mock.get_github_commit_url.side_effect = [
            github_commit_url]

    def _set_excluded_route(self, route):
        del self._excluded_routes[:]
        self._excluded_routes.append(route)

    def test_version_before_render(self):
        """
        Test the version_before_render method

        1. Production
        2. Development
        3. Excluded route
        """
        event = mock.MagicMock()
        event.rendering_val = {}

        # 1. Production
        self._set_version_read('1.2.3')
        request = mock.Mock()
        request.registry.settings = {'c3smembership.runmode': 'prod'}
        event_dict = {'request': request}
        event.__getitem__.side_effect = event_dict.__getitem__
        event.__contains__.side_effect = event_dict.__contains__

        version_before_render(event)
        self.assertEqual(
            event.rendering_val['version_information'],
            'Version 1.2.3')
        self.assertIsNone(event.rendering_val['version_location_name'])
        self.assertIsNone(event.rendering_val['version_location_url'])
        self.assertEqual(len(self._open_mock.mock_calls), 1)

        # 2. Development
        request.registry.settings = {'c3smembership.runmode': 'dev'}
        self._set_version_read('1.2.3')
        self._set_git_tag('my_test_tag')
        self._set_git_branch('some_test_branch')
        self._set_git_get_commit_hash('abcdef123456')
        self._set_git_get_github_commit_url('https://example.com')
        version_before_render(event)
        self.assertTrue(
            'Version 1.2.3' in event.rendering_val['version_information'])
        self.assertTrue(
            'my_test_tag' in event.rendering_val['version_information'])
        self.assertTrue(
            'some_test_branch' in event.rendering_val['version_information'])
        self.assertEqual(
            event.rendering_val['version_location_name'],
            'abcdef123456')
        self.assertEqual(
            event.rendering_val['version_location_url'],
            'https://example.com')
        self.assertEqual(len(self._open_mock.mock_calls), 2)

        # 3. Excluded route
        request = mock.Mock()
        request.matched_route.name = 'some_route'
        event_dict = {'request': request}
        event.get.side_effect = [request]
        self._set_excluded_route('some_route')
        version_before_render(event)
        # Assert that open has not been called again and thus the route
        # exclusion works
        self.assertEqual(len(self._open_mock.mock_calls), 2)
