# -*- coding: utf-8 -*-
"""
Provides mocking classes for testing the pagination module.
"""


from c3smembership.presentation.pagination import IContentSizeProvider
from c3smembership.presentation.pagination.reading import (
    IPaginationReader,
    IReader,
)
from c3smembership.presentation.pagination.pagination import (
    PaginationRequest
)
from c3smembership.presentation.pagination.property_naming import (
    IPropertyNaming
)
from c3smembership.presentation.pagination.url_building import (
    IUrlCreator,
    IUrlCreatorFactory,
)
from c3smembership.presentation.pagination.writing import (
    IPaginationRequestWriter
)
from c3smembership.presentation.pagination.validation import (
    IValidator
)


class ValidatorMock(IValidator):
    # pylint: disable=too-few-public-methods
    """
    Mocks an validation.IValidator callable.

    The callable returns True for the call specified on creation.

    Example::

        >>> validator = ValidatorMock(1)
        >>> validator('some value')
        True
        >>> validator('some other value')
        False
        >>> validator('some third value')
        False

        >>> validator = ValidatorMock(2)
        >>> validator('some value')
        False
        >>> validator('some other value')
        True
        >>> validator('some third value')
        False
    """

    def __init__(self, valid_call):
        """
        Initialises the ValidatorMock object.

        Args:
            valid_call (int): The number of the call for which the ValidatorMock
                returns True. It returns False for all other calls.
        """
        self._valid_call = valid_call
        self._calls = 0

    def __call__(self, value):
        """
        Mocks the validation call and returns True for the call number specified
        at the object's creation.

        Args:
            value: The value to be validated which is ignored by the
                ValidatorMock.

        Returns:
            True for the call specified.
        """
        self._calls += 1
        return self._calls == self._valid_call


class CallCounter(object):
    # pylint: disable=too-few-public-methods
    """
    Counts the number of times a call was executed.
    """

    def __init__(self):
        """
        Initialises the CallCounter object.
        """
        self._call_counters = {}

    def _count_call(self, counter_name=''):
        """
        Counts the call on a named counter.

        Args:
            counter_name (string): The name of the counter to be incremeted.
                The value of this parameter is an empty string representing the
                default counter.
        """
        self._ensure_counter_exists(counter_name)
        self._call_counters[counter_name] += 1

    def _ensure_counter_exists(self, counter_name):
        """
        Ensures that the counter with the specified name exists. If the counter
        does not exist already it is created.

        Args:
            counter_name (string): The name of the counter whose existence is
                ensured.
        """
        if counter_name not in self._call_counters:
            self._call_counters[counter_name] = 0

    @property
    def call_count(self, counter_name=''):
        """
        Get the count of the calls to the named counter.

        Returns:
            An integer representing the number of times the named counter was
            called.
        """
        self._ensure_counter_exists(counter_name)
        return self._call_counters[counter_name]


class CallCallCounter(CallCounter):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super(CallCallCounter, self).__init__()

    def __call__(self, *args, **kwargs):
        self._count_call()
        self._call(*args, **kwargs)

    def _call(self, *args, **kwargs):
        raise NotImplementedError()


class ContentSizeProviderMock(CallCallCounter, IContentSizeProvider):
    # pylint: disable=too-few-public-methods

    def __init__(self, call_result):
        super(ContentSizeProviderMock, self).__init__()
        self._call_result = call_result
        self._request = None

    def _call(self, request):
        self._request = request
        return self._call_result

    def get_request(self):
        return self._request


class MockReader(IReader):
    # pylint: disable=too-few-public-methods

    def __init__(self, result):
        self.__result = result

    def __call__(self):
        return self.__result


class UrlCreatorMock(IUrlCreator):
    # pylint: disable=too-few-public-methods

    def __init__(self, url):
        self.__url = url

    def __call__(self, pagination_request, route_url_kwargs=None):
        return self.__url


class UrlCreatorFactoryMock(IUrlCreatorFactory):
    # pylint: disable=too-few-public-methods

    def __init__(self, url):
        self._url = url

    def __call__(self, request, route_name):
        return UrlCreatorMock(self._url)


class ResponseMock(object):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.__call_count = 0
        self.__cookies = {}

    def set_cookie(self, name, value):
        self.__cookies[name] = value
        self.__call_count += 1

    def get_cookie(self, name):
        return self.__cookies[name]

    def call_count(self):
        return self.__call_count


class RouteMock(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, route_name):
        self.name = route_name


class ContextFoundEventMock(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, request):
        self.request = request


class BeforeRenderEventMock(dict):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super(BeforeRenderEventMock, self).__init__()
        self.rendering_val = {}


class PaginationReaderMock(IPaginationReader):
    # pylint: disable=too-few-public-methods

    def __init__(self, pagination):
        self._pagination = pagination
        self._call_count = 0

    def __call__(self, request, content_size):
        self._call_count += 1
        return self._pagination

    @property
    def call_count(self):
        return self._call_count


class PaginationRequestWriterMock(IPaginationRequestWriter):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self._call_count = 0

    def __call__(self, request, pagination_request):
        self._call_count += 1

    @property
    def call_count(self):
        return self._call_count


class RegistryMock(object):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.pagination = {}


class ConfigurationMock(object):
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.registry = RegistryMock()
        self.directives = {}
        self.subscribers = {}

    def add_directive(self, directive_name, directive_callable):
        assert(directive_name not in self.directives)
        self.directives[directive_name] = directive_callable

    def add_subscriber(self, subscriber, subscriber_interface):
        assert(subscriber_interface not in self.subscribers)
        self.subscribers[subscriber_interface] = subscriber


class PropertyNamingMock(IPropertyNaming):

    def __init__(
            self,
            page_number_name,
            page_size_name,
            sort_property_name,
            sort_direction_name):
        self._page_number_name = page_number_name
        self._page_size_name = page_size_name
        self._sort_property_name = sort_property_name
        self._sort_direction_name = sort_direction_name

    @property
    def page_number_name(self):
        return self._page_number_name

    @property
    def page_size_name(self):
        return self._page_size_name

    @property
    def sort_property_name(self):
        return self._sort_property_name

    @property
    def sort_direction_name(self):
        return self._sort_direction_name
