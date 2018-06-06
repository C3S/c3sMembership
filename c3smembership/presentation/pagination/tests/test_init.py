# -*- coding: utf-8 -*-
"""
"""

from unittest import TestCase
from c3smembership.presentation.pagination import (
    IContentSizeProvider,
    includeme,
    is_pagination_route,
    make_pagination_route,
    PaginationBeforeRenderSubscriber,
    PaginationContextFoundSubscriber,
)
from c3smembership.presentation.pagination.exceptions import (
    PageNotFoundException
)
from c3smembership.presentation.pagination.reading import (
    RequestPaginationReader,
)
from c3smembership.presentation.pagination.writing import (
    DefaultPaginationRequestWriter,
)
from c3smembership.presentation.pagination.pagination import (
    Pagination,
    Paging,
    Sorting,
    PagingRequest,
)
from c3smembership.presentation.parameter_validation import (
    ParameterValidationException
)
from pyramid.testing import DummyRequest
from pyramid.events import (
    BeforeRender,
    ContextFound,
)
from pyramid import testing
from mocking import (
    BeforeRenderEventMock,
    ConfigurationMock,
    ContentSizeProviderMock,
    ContextFoundEventMock,
    PaginationReaderMock,
    PaginationRequestWriterMock,
    PropertyNamingMock,
    RouteMock,
    UrlCreatorFactoryMock,
)


class IContentSizeProviderTest(TestCase):

    def test_call(self):
        content_size_provider = IContentSizeProvider()
        with self.assertRaises(NotImplementedError):
            content_size_provider('request')


class FunctionsTest(TestCase):

    def test_is_pagination_route(self):
        request = DummyRequest()
        request.registry.pagination = {
            'some_route': {}
        }
        request.matched_route = RouteMock('some_route')
        self.assertTrue(is_pagination_route(request))

        request.matched_route = RouteMock('some_other_route')
        self.assertFalse(is_pagination_route(request))

    def test_make_pagination_route(self):
        settings_counter = 9

        # test defaults
        config = ConfigurationMock()
        make_pagination_route(
            config,
            'some_route',
            'some content size provider')
        self.assertTrue('some_route' in config.registry.pagination)
        pagination = config.registry.pagination['some_route']
        self.assertEqual(len(pagination), settings_counter)
        self.assertEqual(
            pagination['content_size_provider'],
            'some content size provider')
        # TODO: Use mock instead of RequestPaginationReader?
        self.assertEqual(
            type(pagination['pagination_reader']),
            RequestPaginationReader)
        self.assertEqual(
            type(pagination['pagination_request_writer']),
            DefaultPaginationRequestWriter)
        self.assertEqual(
            pagination['page_size_default'],
            10)
        self.assertEqual(
            pagination['sort_property_default'],
            '')

        # test everything
        config = ConfigurationMock()
        make_pagination_route(
            config,
            'some_route',
            'some content size provider',
            pagination_reader='some pagination reader',
            pagination_request_writer='some pagination request writer',
            sort_property_default='some sort property default',
            sort_direction_default='desc',
            page_size_default=123,
            page_number_default=9)
        self.assertTrue('some_route' in config.registry.pagination)
        pagination = config.registry.pagination['some_route']
        self.assertEqual(len(pagination), settings_counter)
        self.assertEqual(
            pagination['content_size_provider'],
            'some content size provider')
        self.assertEqual(
            pagination['pagination_reader'],
            'some pagination reader')
        self.assertEqual(
            pagination['pagination_request_writer'],
            'some pagination request writer')
        self.assertEqual(
            pagination['page_size_default'],
            123)
        self.assertEqual(
            pagination['sort_property_default'],
            'some sort property default')
        self.assertEqual(
            pagination['sort_direction_default'],
            'desc')
        self.assertEqual(
            pagination['page_number_default'],
            9)

        # test duplicate configuration fails
        config = ConfigurationMock()
        make_pagination_route(
            config,
            'some_route',
            'some content size provider')
        with self.assertRaises(ValueError):
            make_pagination_route(
                config,
                'some_route',
                'some content size provider')

    def test_includeme(self):
        config = ConfigurationMock()
        includeme(config)
        self.assertEqual(len(config.subscribers), 2)
        self.assertEqual(len(config.directives), 1)
        self.assertEqual(
            type(config.subscribers[BeforeRender]),
            PaginationBeforeRenderSubscriber)
        self.assertEqual(
            type(config.subscribers[ContextFound]),
            PaginationContextFoundSubscriber)
        self.assertEqual(
            config.directives['make_pagination_route'],
            make_pagination_route)


class PaginationContextFoundSubscriberTest(TestCase):

    def test_call(self):
        pagination_reader = PaginationReaderMock('some pagination')
        content_size_provider_mock = ContentSizeProviderMock(100)

        request = DummyRequest()
        request.registry.pagination = {
            'some_route': {
                'content_size_provider': content_size_provider_mock,
                'pagination_reader': pagination_reader,
            }
        }
        request.matched_route = RouteMock('some_route')

        event = ContextFoundEventMock(request)
        subscriber = PaginationContextFoundSubscriber()
        subscriber(event)
        self.assertEqual(request.pagination, 'some pagination')
        self.assertEqual(pagination_reader.call_count, 1)
        self.assertEqual(content_size_provider_mock.call_count, 1)
        self.assertEqual(content_size_provider_mock.get_request(), request)


    def test_call_exception(self):

        class ExceptionPaginationReader(object):
            # pylint: disable=too-few-public-methods

            def __init__(self, exception):
                self._exception = exception

            def __call__(self, request, content_size_provider):
                raise self._exception


        content_size_provider_mock = ContentSizeProviderMock(100)

        request = DummyRequest()
        request.registry.pagination = {
            'some_route': {
                'content_size_provider': content_size_provider_mock,
                'pagination_reader': ExceptionPaginationReader(
                    PageNotFoundException()),
            }
        }
        request.matched_route = RouteMock('some_route')

        event = ContextFoundEventMock(request)
        subscriber = PaginationContextFoundSubscriber()
        with self.assertRaises(ParameterValidationException):
            subscriber(event)


class PaginationBeforeRenderSubscriberTest(TestCase):

    def test_call(self):
        config = testing.setUp()
        config.add_route('some_route', '/')

        pagination_request_writer = PaginationRequestWriterMock()
        param_property_naming = PropertyNamingMock(
            'page-number',
            'page-size',
            'sort-property',
            'sort-direction')
        url_creator_factory = UrlCreatorFactoryMock('http://example.com')
        request = DummyRequest()
        request.registry.pagination = {
            'some_route': {
                'pagination_request_writer': pagination_request_writer,
                'param_property_naming': param_property_naming,
                'url_creator_factory': url_creator_factory,
            }
        }
        request.pagination = Pagination(
            Paging(
                100,
                PagingRequest(3, 12)),
            Sorting('some_property', 'desc'))
        request.matched_route = RouteMock('some_route')
        event = BeforeRenderEventMock()
        event['request'] = request
        subscriber = PaginationBeforeRenderSubscriber()
        subscriber(event)
        self.assertEqual(pagination_request_writer.call_count, 1)

        pagination = event.rendering_val['pagination']
        self.assertEqual('http://example.com', str(pagination.url))
