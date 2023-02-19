# -*- coding: utf-8 -*-
"""
Utilities for creating URLs.
"""

from .pagination import (
    Pagination,
    Sorting,
)


class IUrlCreator(object):
    # pylint: disable=too-few-public-methods
    """
    Interface of the url creator callable.
    """

    def __call__(self, pagination_request, route_url_kwargs=None):
        """
        Creates a url according to the pagination request and url parameters.

        Args:
            pagination_request: The pagination request for which the URL is
                created.
            route_url_kwargs: The kwargs passed to the ``request.route_url``
                call.

        Returns:
            The of for the pagination request.
        """
        raise NotImplementedError()


class RequestUrlCreator(IUrlCreator):
    # pylint: disable=too-few-public-methods

    def __init__(self, request, route_name, param_property_naming):
        self._request = request
        self._route_name = route_name
        self._param_property_naming = param_property_naming

    def __call__(self, pagination_request, route_url_kwargs=None):
        if route_url_kwargs is None:
            route_url_kwargs = {}
        if '_query' not in route_url_kwargs:
            route_url_kwargs['_query'] = {}

        # keep matchdict values
        for key, value in list(self._request.matchdict.items()):
            route_url_kwargs[key] = value

        # keep original query parameters
        for key, value in list(self._request.GET.items()):
            route_url_kwargs['_query'][key] = value

        paging_request = pagination_request.paging_request
        sorting = pagination_request.sorting

        page_number_name = self._param_property_naming.page_number_name
        page_size_name = self._param_property_naming.page_size_name
        sort_property_name = self._param_property_naming.sort_property_name
        sort_direction_name = self._param_property_naming.sort_direction_name
        route_url_kwargs['_query'][page_number_name] = \
            paging_request.page_number
        route_url_kwargs['_query'][page_size_name] = paging_request.page_size
        route_url_kwargs['_query'][sort_property_name] = sorting.sort_property
        route_url_kwargs['_query'][sort_direction_name] = sorting.sort_direction

        return self._request.route_url(self._route_name, **route_url_kwargs)


class IUrlCreatorFactory(object):
    # pylint: disable=too-few-public-methods
    """
    Factory to create instances of IUrlCreator. The factory is used to
    instanciate IUrlCreator objects which then are used to create the paging
    URLs to specific pages.
    """

    def __call__(self, request, route_name):
        """
        Creates a URL for the route name.

        Args:
            request: The request currently being processed.
            route_name: The name of the route for which the URL must is created.

        Returns:
            A string representing the URL for the specified route name.
        """
        raise NotImplementedError()


class RequestUrlCreatorFactory(IUrlCreatorFactory):
    # pylint: disable=too-few-public-methods
    """
    Factory to create instances of IUrlCreator from request parameters.
    """

    def __init__(self, param_property_naming):
        """
        Initializes the RequestUrlCreatorFactory.

        Args:
            param_property_naming: The parameter property naming which is used
                to create the IUrlCreator.
        """
        self._param_property_naming = param_property_naming

    def __call__(self, request, route_name):
        """
        Creates a URL for the route name.

        Args:
            request: The request currently being processed.
            route_name: The name of the route for which the URL must is created.

        Returns:
            A string representing the URL for the specified route name.
        """
        return RequestUrlCreator(
            request,
            route_name,
            self._param_property_naming)


class UrlBuilder(object):
    """
    A builder for pagination URLs.
    """

    def __init__(self, url_creator, pagination):
        """
        Initializes the ``UrlBuilder`` object.
        """
        self.__url_creator = url_creator
        self.__pagination = pagination

    @property
    def pagination(self):
        """
        Returns the pagination of the URL builder.
        """
        return self.__pagination

    def _change_paging(self, paging):
        """
        Returns a ``UrlBuilder`` object with given paging information.
        """
        return UrlBuilder(
            self.__url_creator,
            Pagination(
                paging,
                self.__pagination.sorting
            )
        )

    def _change_sorting(self, sorting):
        """
        Returns a ``UrlBuilder`` object with given sorting information.
        """
        return UrlBuilder(
            self.__url_creator,
            Pagination(
                self.__pagination.paging,
                sorting
            )
        )

    def sort_direction(self, sort_direction):
        """
        Returns a ``UrlBuilder`` object with the specified sort direction.
        """
        return self._change_sorting(
            Sorting(
                self.__pagination.sorting.sort_property,
                sort_direction,
            )
        )

    def sort_property(self, sort_property):
        """
        Returns a ``UrlBuilder`` object with the specified sort property.
        """
        return self._change_sorting(
            Sorting(
                sort_property,
                self.__pagination.sorting.sort_direction,
            )
        )

    @property
    def first_page(self):
        """
        Returns a ``UrlBuilder`` object for the first page.
        """
        return self._change_paging(self.__pagination.paging.first_page)

    @property
    def last_page(self):
        """
        Returns a ``UrlBuilder`` object for the last page.
        """
        return self._change_paging(self.__pagination.paging.last_page)

    @property
    def previous_page(self):
        """
        Returns a ``UrlBuilder`` object for the previous page.
        """
        return self._change_paging(self.__pagination.paging.previous_page)

    @property
    def next_page(self):
        """
        Returns a ``UrlBuilder`` object for the next page.
        """
        return self._change_paging(self.__pagination.paging.next_page)

    @property
    def invert_sort_direction(self):
        """
        Returns a ``UrlBuilder`` object with inverted sort direction.
        """
        if self.__pagination.sorting.sort_direction == 'asc':
            return self.sort_direction('desc')
        else:
            return self.sort_direction('asc')

    def sort_property_alternating_direction(self, sort_property):
        """
        Returns a ``UrlBuilder`` object for the sort property. If the current
        object is already sorted on the same property then the sort direction
        is inverted.

        Args:
            sort_property: The name of the sort property on which the returned
                ``UrlBuilder`` is sorted.
        """
        if self.__pagination.sorting.sort_property == sort_property:
            return self.invert_sort_direction
        else:
            return self.sort_property(sort_property).sort_direction('asc')

    def __str__(self):
        """
        Returns the actual pagination URL.
        """
        return self.url

    @property
    def url(self):
        """
        Returns the actual pagination URL.
        """
        return self.__url_creator(self.__pagination)
