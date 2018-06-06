# -*- coding: utf-8 -*-
"""
The pagination extension for Pyramid offers simple to use pagination
functionality.

Example::

    >>> from pyramid.config import Configurator
    >>> from pyramid.view import view_config
    >>>
    >>> content = range(1000)
    >>>
    >>> def content_size_provider(request):
    ...     return len(content)
    ...
    >>> @view_config(route_name='some_route', renderer='json')
    >>> def some_view(request):
    ...     paging = request.pagination.paging
    ...     first_element = paging.content_offset + 1
    ...     last_element = first_element + paging.page_size
    ...     return content[first_element:last_element]
    ...
    >>> config = Configurator()
    >>> config.include('pagination')
    >>> config.add_route('some_route', '/')
    >>> config.make_pagination_route('some_route', content_size_provider)
    >>> config.scan()

Design considerations:

Pagination information is expected to be part of the query component of the URL
and not the path component. In Pyramid terms it is determined from
request.params and not from request.matchdict. The reason for this is URL design
best practices. Pagination is a type of filtering displaying only a specified
subset of the complete collection. See Marke Massé "REST API Design Rulebook"
pages 19 and 20. If for some reason pagination information must be part of the
path component of the URL, the pagination extension' make_pagination_route
method can be provided with an implementation of the reading.IPaginationReader
callable as the pagination_reader attribute which retrieves the pagination
information from the path component of the URL as well as a UrlBuilder for
building the page URLs in the templates.

The following features are not implemented yet but could be considered for
future development:

- Multiple sorting: Sorting can be performed on multiple columns, e.g. by
  country, region, city and postal code. In this scenario sort property and
  sort direction cannot be single values but must be a list of property and
  direction pairs.
- Null and none sorting: The handling of null and none values could be
  configured specifying whether null and none values appear first or last in a
  sorted data set.
- Filtering: Data sets could be filtered which affects the pagination. Filtering
  determines the number of entries of a data set. Therefore,
  IContentSizeProvider must be extended by filterin in order to determine the
  content size of the filtered data set.

Interfaces:

The interfaces specified in this package exist for explicitly stating the design
as well as for documentation purposes. Python as a dynamically typed language
does not require their existence or use.

Example::

    >>> from c3smembership.presentation.pagination.reading import IReader
    >>> class SimpleReader(IReader)
    ...     def __call__(self):
    ...         return 'test'
    ...
    >>> reader_callable = SimpleReader()
    >>> reader_callable()
    'test'

Example::

    >>> def simple_reader():
    ...     return 'test'
    ...
    >>> reader_callable = simple_reader
    'test'

Example::

    >>> from c3smembership.presentation.pagination.reading import IReader
    >>> class FileReader(IReader):
    ...     def __init__(self, filename):
    ...         self._filename = filename
    ...     def __call__(self):
    ...         with open(self._filename, 'r') as file:
    ...             return file.read()
    ...
    >>> reader_callable = FileReader('testfile.txt')
    >>> reader_callable()
    'This is the content of testfile.txt.'

Example::

    >>> def file_reader(filename):
    ...     def reader():
    ...         with open(filename, 'r') as file:
    ...             return file.read()
    ...     return reader
    ...
    >>> reader_callable = file_reader('testfile.txt')
    >>> reader_callable()
    'This is the content of testfile.txt.'
"""

# TODO:
#
# - When /dashboard is requested and cookie information is found, a different
#   page than page 1 might be displayed at /dashboard. This might violate URL
#   resource identification rules. The machanism for redirecting to cookie
#   stored pagination could be handled from a dialog flow outside the pagination
#   package. Therefore, this information might need to be provided.
# - Offer post names to templates, e.g. pagination.post_property_naming
#   (PropertyNaming), in order to fill form field names automatically.
# - pagination.ui: offer ways to generate table headers including title, sorting
#   links, alternate sorting link. Input: Title, sort property name, header
#   template (configuring what to show: sorting, no sorting, etc.).
# - Offer easy ways to indicate which column is sorted on in which direction.

from .exceptions import PageNotFoundException
from .property_naming import PropertyNaming
from .reading import (
    RequestPaginationReader,
)
from .url_building import (
    UrlBuilder,
    RequestUrlCreatorFactory
)
from .writing import (
    DefaultPaginationRequestWriter,
)
from c3smembership.presentation.parameter_validation import (
    ParameterValidationException,
)
from .renderer_information import (
    RendererInformation
)
from pyramid.httpexceptions import HTTPFound
from pyramid.events import (
    BeforeRender,
    ContextFound,
)


class IContentSizeProvider(object):
    # pylint: disable=too-few-public-methods
    """
    Provides the content size for pagination.

    The content size provider is a ``python callable`` which accepts no
    parameters and returns the content size for pagination. The content size is
    subject to the individual type of content and must therefore be provided to
    the pagination package.

    This interface is available for documentation purposes in order to define
    the structure of the ``python callable`` which must be passed as a
    content size provider.

    Example:
        The content size provider ``python callable`` may be a method::

            my_data = [1, 2, 3]

            def some_content_size_provider(request):
                return len(my_data)

    Example:
        The ``python callable`` can also be implemented as a class providing
        the magic method __call__.
        ::

            class DictionaryContentSizeProvider(IContentSizeProvider):

                def __init__(self, dictionary):
                    self._dictionary = dictionary

                def __call__(self):
                    return len(self._dictionary)

            my_dict = {}
            content_size_provider = DictionaryContentSizeProvider(my_dict)
    """

    def __call__(self, request):
        """
        Returns the content size for pagination.

        Args:
            request: The pyramid.request.Request object of the current request.
        """
        raise NotImplementedError()


def is_pagination_route(request):
    """
    Returns whether the ``request.matched_route`` is configured as a
    pagination route.
    """
    return request.matched_route is not None \
        and request.matched_route.name in request.registry.pagination


class PaginationContextFoundSubscriber(object):
    # pylint: disable=too-few-public-methods
    """
    Instances of this class can be used as subscribers to the
    ``pyramid.events.ContextFound`` event in order to provide pagination
    information to the pyramid view callable handling the route.

    Pagination information is provided to the pyramid view callable via the
    ``request.pagination`` attribute as a ``Pagination`` object.
    """

    def __call__(self, event):
        """
        Provides the ``request.pagination`` attribute to the pyramid view
        callable.
        """
        request = event.request
        if is_pagination_route(request):
            settings = request.registry.pagination[request.matched_route.name]
            content_size_provider = settings['content_size_provider']
            pagination_reader = settings['pagination_reader']
            try:
                request.pagination = pagination_reader(
                    request,
                    content_size_provider(request))
            except PageNotFoundException:
                raise ParameterValidationException(
                    'Page does not exist.',
                    request.route_url(request.matched_route.name))


class PaginationBeforeRenderSubscriber(object):
    # pylint: disable=too-few-public-methods
    """
    Instances of this class can be used as subscribers to the
    ``pyramid.events.BeforeRender`` event in order to provide pagination
    information to the rendering templates.
    """

    def __call__(self, event):
        """
        Provides the ``pagination`` object to rendering templates and stores
        the pagination information in cookies.
        """
        request = event.get('request')
        if is_pagination_route(request) and hasattr(request, 'pagination'):
            pagination = request.pagination

            settings = request.registry.pagination[request.matched_route.name]
            pagination_request_writer = settings['pagination_request_writer']
            pagination_request_writer(request, request.pagination)

            url_creator_factory = settings['url_creator_factory']
            event.rendering_val['pagination'] = RendererInformation(
                UrlBuilder(
                    url_creator_factory(
                        request,
                        request.matched_route.name),
                    pagination
                ),
                pagination.paging,
                pagination.sorting,
            )


def make_pagination_route(
        config,
        route_name,
        content_size_provider,
        pagination_reader=None,
        pagination_request_writer=None,
        page_number_default=1,
        page_size_default=10,
        sort_property_default='',
        sort_direction_default='asc',
        url_creator_factory=None):
    # pylint: disable=too-many-arguments
    """
    Makes a route into a pagination route.

    Pagination routes are provided with a ``Pagination`` object via
    ``request.pagination`` which offers pagination information.

    Args:
        config (pyramid.config.Configurator): The object to which the route
            belongs.
        route_name (str): The name of the route.
        content_size_provider (IContentSizeProvider): A python callable.
        sort_property_default (str): The name of the default sort property which is
            used in case nothing else is specified.
        page_size_default (int): The default page size in case nothing else is
            specified.
    """
    if route_name in config.registry.pagination:
        raise ValueError('Route already registered.')
    post_property_naming = PropertyNaming(
        'page_number',
        'page_size',
        'sort_property',
        'sort_direction'
    )
    param_property_naming = PropertyNaming(
        'page-number',
        'page-size',
        'sort-property',
        'sort-direction'
    )
    cookie_property_naming = PropertyNaming(
        'page_number',
        'page_size',
        'sort_property',
        'sort_direction',
        route_name + '.{property_name}'
    )

    if pagination_reader is None:
        pagination_reader = RequestPaginationReader(
            post_property_naming,
            param_property_naming,
            cookie_property_naming
        )
    if pagination_request_writer is None:
        pagination_request_writer = DefaultPaginationRequestWriter(
            cookie_property_naming)
    if url_creator_factory is None:
        url_creator_factory = RequestUrlCreatorFactory(param_property_naming)
    config.registry.pagination[route_name] = {
        'content_size_provider': content_size_provider,
        'pagination_reader': pagination_reader,
        'pagination_request_writer': pagination_request_writer,
        'page_number_default': page_number_default,
        'page_size_default': page_size_default,
        'sort_property_default': sort_property_default,
        'sort_direction_default': sort_direction_default,
        'param_property_naming': param_property_naming,
        'url_creator_factory': url_creator_factory,
    }


def includeme(config):
    """
    Hook for pyramid plugins.

    This method is called when the plugin is included into the pyramid
    application's configuration using the ``pyramid.Configurator.include()``
    method.

    It is not necessary to call this method directly.

    Example:

        ::

            from pyramid.config import Configurator
            config = Configurator()
            config.include('pagination')
    """
    config.registry.pagination = {}
    config.add_directive('make_pagination_route', make_pagination_route)
    config.add_subscriber(PaginationContextFoundSubscriber(), ContextFound)
    config.add_subscriber(PaginationBeforeRenderSubscriber(), BeforeRender)
