# -*- coding: utf-8 -*-
"""
The pagination package defines general classes which store pagination
information. They are independent of Pyramid.
"""

from .exceptions import PageNotFoundException


class PagingRequest(object):
    """
    Provides information about paging request, i.e. the request of a particular
    page. This paging request is used to store information about the page which
    the user requests.

    Paging requests consist of a page number and a page size which are
    requested. A paging request does not contain information about the size of
    the content from which the page is requested. It calculates the content
    offset of the page and can check whether page number and page size have
    valid values for a certain content size.
    """

    def __init__(self, page_number, page_size):
        """
        Initializes the PagingRequest object.

        Args:
            page_number: The number of the requested page. Must be a positive
                integer of type int.
            page_size: The size of the requested page. Must be a positive
                integer of type int.

        Raises:
            TypeError: In case page_number or page_size are not of type int.
            ValueError: In case page_number or page_size are not larger than
                zero.
        """
        if not isinstance(page_number, int):
            raise TypeError('Parameter page_number must be of type int.')
        if not page_number > 0:
            raise ValueError('Parameter page_number must be larger than zero.')
        if not isinstance(page_size, int):
            raise TypeError('Parameter page_size must be of type int.')
        if not page_size > 0:
            raise ValueError('Parameter page_size must be larger than zero.')
        self.__page_number = page_number
        self.__page_size = page_size

    @property
    def page_number(self):
        """
        The page number.
        """
        return self.__page_number

    @property
    def page_size(self):
        """
        The page size, i.e. the number of content items displayed per page.
        """
        return self.__page_size

    @property
    def content_offset(self):
        """
        The content offset, i.e. the number of content items which reside on all
        previous pages.

        For instance, the content offset of page 3 with page size 10 is 20. The
        pages 1 and 2 with each contain 10 content items, page 1 items 1 to 10
        and page 2 items 11 to 20. Page 3 therefore starts with content item 21.
        """
        return (self.page_number - 1) * self.page_size

    def is_valid_content_size_page(self, content_size):
        """
        Determines whether ``page_number`` exists for ``page_size`` and the
        specified parameter ``content_size``.
        """
        return self.content_offset < max(content_size, 1)


class Paging(PagingRequest):
    """
    Provides paging functionality.

    Paging information consist of a paging request (page number and page size)
    as well as the actual content size.
    """

    def __init__(self, content_size, paging_request):
        """
        Initializes the Paging object.

        The content size must be valid for the page number and page size of the
        paging request.

        Args:
            content_size: The size of the content which is paged. Must be of
                type int.
            paging_request: A ``PagingRequest`` object providing the page number
                and page size.

        Raises:
            TypeError: In case content_size is not of type int.
            ValueError: In case content_size is not equal to or larger than
                zero.
            PageNotFoundException: In case the page number of paging_request
                does not exist with the given content_size and page size of
                paging_request.
        """
        PagingRequest.__init__(
            self,
            paging_request.page_number,
            paging_request.page_size)
        if not isinstance(content_size, int):
            raise TypeError('Parameter content_size must be of type int.')
        if not content_size >= 0:
            raise ValueError(
                'Paramter content_size must be equal to or larger than zero.')
        self.__content_size = content_size
        if not paging_request.page_number <= self._last_page_number:
            raise PageNotFoundException('Page does not exist.')

    def __iter__(self):
        """
        Returns an iterator to scroll through the pages.
        """
        return PagingIterator(self)

    @property
    def content_size(self):
        """
        Returns the size of the content.
        """
        return self.__content_size

    @property
    def page_count(self):
        """
        Returns number of pages the content size is split into considering the page
        size.
        """
        return self._last_page_number - \
            self._first_page_number + 1

    @property
    def next_page(self):
        """
        Returns a ``Paging`` object representing the next page of the current
        page number.

        Raises:
            PageNotFoundException: In case the content does not have a next
                page. Use the property ``has_next_page`` in order to determine
                whether a next page exists.
        """
        if not self.has_next_page:
            raise PageNotFoundException('A next page does not exist.')
        return self.page(self.page_number + 1)

    @property
    def previous_page(self):
        """
        Returns a ``Paging`` object representing the previous page of the
        current page number.

        Raises:
            PageNotFoundException: In case the content does not have a
                previous page. Use the property ``has_previous_page`` in order
                to determine whether a next page exists.
        """
        if not self.has_previous_page:
            raise PageNotFoundException('A previous page does not exist.')
        return self.page(self.page_number - 1)

    def page(self, page_number):
        """
        Gets the ``Paging`` object of a specific page number.

        Args:
            page_number: The page number of the page to be returned.

        Raises:
            PageNotFoundException: In case the content does not have a
                page with the specified page number. Use the method ``has_page``
                in order to determine whether a page with this page number is
                exists.
        """
        if not self.has_page(page_number):
            raise PageNotFoundException(
                'Page {page_number} does not exist.'.format(
                    page_number=page_number))
        return Paging(
            self.content_size,
            PagingRequest(page_number, self.page_size))

    @property
    def first_page(self):
        """
        Returns a ``Paging`` object representing the first page of the content.
        """
        return self.page(self._first_page_number)

    @property
    def last_page(self):
        """
        Returns a ``Paging`` object representing the last page of the content.
        """
        return self.page(self._last_page_number)

    @property
    def is_first_page(self):
        """
        Determines whether the current page is the first page of the content.
        """
        return self.page_number == self._first_page_number

    @property
    def is_last_page(self):
        """
        Determines whether the current page is the last page of the content.
        """
        return self.page_number == self._last_page_number

    @property
    def _first_page_number(self):
        """
        Returns the number of the first page of the content.
        """
        return 1

    @property
    def _last_page_number(self):
        """
        Returns the number of the last page of the content.

        In case the content does not contain any items there is still one empty
        page.
        """
        return (max(self.content_size, 1) - 1) // self.page_size + 1

    def has_page(self, page_number):
        """
        Determines whether the content contains a page with a given page number.

        Args:
            page_number: The number of the page.
        """
        return page_number >= self._first_page_number \
            and page_number <= self._last_page_number

    @property
    def has_next_page(self):
        """
        Determines whether the content has a next page.
        """
        return self.has_page(self.page_number + 1)

    @property
    def has_previous_page(self):
        """
        Determines whether the content has a previous page.
        """
        return self.has_page(self.page_number - 1)


class PagingIterator(Paging):
    """
    An iterator to scroll through pages of a content.
    """

    def __init__(self, paging):
        """
        Initializes the ``PagingIterator`` object.

        Args:
            paging: The ``Paging`` object to be iterated.
        """
        super(PagingIterator, self).__init__(
            paging.content_size,
            PagingRequest(
                paging.page_number,
                paging.page_size))
        self.__iter_position = paging.page_number - 1

    def __iter__(self):
        """
        Returns the iterator.
        """
        return self

    def __next__(self):
        """
        Returns the next object in iteration.

        Python3 compatible.
        """
        return self.next()

    def next(self):
        """
        Returns the next object in iteration.

        Python2 compatible.
        """
        if self.__iter_position < self.last_page.page_number:
            self.__iter_position += 1
            return self.page(self.__iter_position)
        else:
            raise StopIteration()


class Sorting(object):
    """
    Contains sorting information.

    The sorting mechanism is implemented in a simple way. Currently, there is
    only one sort property and the direction in which the property is sorted.
    Multiple sort properties and their directions may be implemented in the
    future.
    """

    def __init__(self, sort_property, sort_direction):
        """
        Initializes the ``Sorting`` object.
        """
        self.__sort_property = sort_property
        self.__sort_direction = sort_direction

    @property
    def sort_property(self):
        """
        Returns the name of the sort property.
        """
        return self.__sort_property

    @property
    def sort_direction(self):
        """
        Returns the sort direction on which the sort property is sorted.
        """
        return self.__sort_direction


class PaginationRequest(object):
    """
    Provides pagination request information which consists of a paging request
    and sorting.
    """

    def __init__(self, paging_request, sorting):
        """
        Initializes the ``PaginationRequest`` object.
        """
        self.__paging_request = paging_request
        self.__sorting = sorting

    @property
    def paging_request(self):
        """
        Returns the ``PagingRequest`` object of this pagination request.
        """
        return self.__paging_request

    @property
    def sorting(self):
        """
        Returns the ``Sorting`` object of this pagination request.
        """
        return self.__sorting


class Pagination(PaginationRequest):
    """
    Provides pagination information including paging and sorting.
    """

    def __init__(self, paging, sorting):
        """
        Initializes the ``Pagination`` object.
        """
        super(Pagination, self).__init__(
            paging,
            sorting
        )

        self.__paging = paging

    @property
    def paging(self):
        """
        Returns the ``Paging`` object of this pagination.
        """
        return self.__paging
