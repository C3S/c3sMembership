# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.before_render_events module
"""

import unittest

import mock

from c3smembership.presentation import before_render_events
from c3smembership.presentation.before_render_events import (
    version_before_render,
    get_version_information,
    get_version_location_name,
    get_version_location_url,
)


class TestVersionBeforeRender(unittest.TestCase):
    """
    Test the version_before_render method
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, methodName='runTest'):
        super(TestVersionBeforeRender, self).__init__(methodName)
        self._read_mock = None

    def setUp(self):
        """
        Set up the test case including mocks and dependency injection

        TODO: This is dependency injection the dirty way and needs to be clean
        up
        """
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

        get_version_information.expire_cache()
        get_version_location_name.expire_cache()
        get_version_location_url.expire_cache()

    def tearDown(self):
        """
        Tear down the test case by reversing dependency injection
        """
        before_render_events.os = self._original_os
        before_render_events.GitTools = self._original_git_tools
        before_render_events.EXCLUDED_ROUTES = self._original_excluded_routes
        before_render_events.open = open

    def _set_version_read(self, version):
        """
        Set mocks to provide the version

        Args:
            version: String. The version to be returned by the version mock.
        """
        self._read_mock = mock.Mock()
        self._read_mock.read.side_effect = [version]
        self._open_mock.side_effect = [self._read_mock]

    def _set_git_tag(self, tag):
        """
        Set mocks to provide the tag

        Args:
            tag: String. The tag to be returned by the tag mock.
        """
        self._git_tools_mock.get_tag.side_effect = [tag]

    def _set_git_branch(self, branch):
        """
        Set mocks to provide the branch

        Args:
            branch: String. The branch to be returned by the branch mock.
        """
        self._git_tools_mock.get_branch.side_effect = [branch]

    def _set_git_get_commit_hash(self, commit_hash):
        """
        Set mocks to provide the commit has

        Args:
            commit_hash: String. The commit hash to be returned by the commit
                hash mock.
        """
        self._git_tools_mock.get_commit_hash.side_effect = [commit_hash]

    def _set_git_get_github_commit_url(self, github_commit_url):
        """
        Set mocks to provide the Github commit URL

        Args:
            github_commit_url: String. The Github commit URL to be returned by
                the mock.
        """
        self._git_tools_mock.get_github_commit_url.side_effect = [
            github_commit_url]

    def _set_excluded_route(self, route):
        """
        Set one excluded route
        """
        del self._excluded_routes[:]
        self._excluded_routes.append(route)

    def test_version_before_render(self):
        """
        Test the version_before_render method

        1. Normal route
        2. Excluded route
        """
        event = mock.MagicMock()
        event.rendering_val = {}
        request = mock.Mock()
        event_dict = {'request': request}
        event.__getitem__.side_effect = event_dict.__getitem__
        event.__contains__.side_effect = event_dict.__contains__

        # 1. Normal route
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
        self.assertEqual(len(self._open_mock.mock_calls), 1)

        # 2. Excluded route
        request = mock.Mock()
        request.matched_route.name = 'some_route'
        event_dict = {'request': request}
        event.get.side_effect = [request]
        self._set_excluded_route('some_route')
        version_before_render(event)
        # Assert that open has not been called again and thus the route
        # exclusion works
        self.assertEqual(len(self._open_mock.mock_calls), 1)

    def test_get_version_information(self):
        """
        Test the cached get_version_information method

        1. Initialize cache
        2. Use cache
        """
        self.assertEqual(len(self._open_mock.mock_calls), 0)

        # 1. Initialize cache
        self._set_version_read('1.2.3')
        self._set_git_tag('my_test_tag')
        self._set_git_branch('some_test_branch')

        version_information = get_version_information()
        self.assertEqual(len(self._open_mock.mock_calls), 1)
        self.assertTrue(
            'Version 1.2.3' in version_information)
        self.assertTrue(
            'my_test_tag' in version_information)
        self.assertTrue(
            'some_test_branch' in version_information)

        # 2. Use cache
        self._set_version_read('1.2.4')
        self._set_git_tag('my_other_tag')
        self._set_git_branch('some_other_branch')

        version_information = get_version_information()
        self.assertEqual(len(self._open_mock.mock_calls), 1)
        self.assertTrue(
            'Version 1.2.3' in version_information)
        self.assertTrue(
            'my_test_tag' in version_information)
        self.assertTrue(
            'some_test_branch' in version_information)

    def test_get_version_location_name(self):
        """
        Test the cached get_version_location_name method

        1. Initialize cache
        2. Use cache
        """
        self.assertEqual(
            len(self._git_tools_mock.get_commit_hash.mock_calls), 0)

        # 1. Initialize cache
        self._set_git_get_commit_hash('abcdef123456')

        version_location_name = get_version_location_name()
        self.assertEqual(
            len(self._git_tools_mock.get_commit_hash.mock_calls), 1)
        self.assertEqual(version_location_name, 'abcdef123456')

        # 2. Use cache
        self._set_git_get_commit_hash('test987654321')

        version_location_name = get_version_location_name()
        self.assertEqual(
            len(self._git_tools_mock.get_commit_hash.mock_calls), 1)
        self.assertEqual(version_location_name, 'abcdef123456')

    def test_get_version_location_url(self):
        """
        Test the cached get_version_location_url method

        1. Initialize cache
        2. Use cache
        """
        self.assertEqual(
            len(self._git_tools_mock.get_github_commit_url.mock_calls), 0)

        # 1. Initialize cache
        self._set_git_get_github_commit_url('https://test1.example.com')

        version_location_url = get_version_location_url()
        self.assertEqual(
            len(self._git_tools_mock.get_github_commit_url.mock_calls), 1)
        self.assertEqual(version_location_url, 'https://test1.example.com')

        # 2. Use cache
        self._set_git_get_github_commit_url('https://test2.example.com')

        version_location_url = get_version_location_url()
        self.assertEqual(
            len(self._git_tools_mock.get_github_commit_url.mock_calls), 1)
        self.assertEqual(version_location_url, 'https://test1.example.com')
