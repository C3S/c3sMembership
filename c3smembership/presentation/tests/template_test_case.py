# -*- coding: utf-8 -*-
"""
Base class for template rendering tests
"""

import unittest

from pyramid import renderers
from pyramid.testing import DummyRequest
import pyramid.testing


class TemplateTestCase(unittest.TestCase):
    """
    Test template rendering
    """

    def __init__(self, methodName, template_path, routes):
        """
        Initialize the TemplateTestCase instance

        This class can be used instead of unittest.TestCase to build template
        test cases.

        Args:
            methodName: Name of the method to be executed. The value is passed
                to the unittest.TestCase.__init__ method.
            template_path: String. The path of the chameleon template to be
                used for rendering
            route: List of string tuples. The routes to be configured for
                rendering.

        Example:
            >>> class TestMemberTemplate(TemplateTestCase):
            ...     def __init__(self, methodName='runTest'):
            ...         super(TestMemberTemplate, self).__init__(
            ...             methodName,
            ...             'member.pt',
            ...             [('member', /member/{number}')])
        """
        super(TemplateTestCase, self).__init__(methodName)
        self._template_path = template_path
        self._routes = routes

    def setUp(self):
        """
        Set up the test configuration for chameleon rendering and add routes
        """
        self.config = pyramid.testing.setUp()
        self.config.include('pyramid_chameleon')
        for route in self._routes:
            self.config.add_route(
                route[0],
                route[1])

    def render(self, values):
        """
        Render the values and return the rendered HTML
        """
        request = DummyRequest()
        return renderers.render(
            self._template_path,
            values,
            request)

    def tearDown(self):
        """
        Tear down the test configuration
        """
        pyramid.testing.tearDown()
