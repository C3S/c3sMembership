# -*- coding: utf-8 -*-
"""
Provide a cache decorator for functions to cache their results

Example:

    >>> from c3smembership.cache import cached
    >>> from datetime import timedelta
    >>> import time
    >>>
    >>> def duration_provider():
    ...     return timedelta(seconds=1)
    ...
    >>> @cached(duration_provider)
    ... def my_func():
    ...     print('\nFilling cache by executing my_func()\n')
    ...     return 'my_func result'
    ...
    >>> my_func()

    Filling cache by executing my_func()

    'my_func result'
    >>> my_func()
    'my_func result'
    >>> time.sleep(1)
    >>> my_func()

    Filling cache by executing my_func()

    'my_func result'
"""

from datetime import (
    timedelta,
    datetime,
)
import hashlib


class CacheWrapper(object):
    """
    The cache wrapper
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, cache):
        """
        Initialize the CacheWrapper object

        Args:
            cache: The Cache object which handles the caching
        """
        self._cache = cache

    def __call__(self, *args, **kwargs):
        """
        Handle the function call in a cached way
        """
        return self._cache.wrapper(*args, **kwargs)

    def expire_cache(self):
        """
        Expire the cache
        """
        self._cache.expire_cache()


def default_duration_provider():
    """
    Provide the cache duration
    """
    return timedelta(hours=4)


class Cache(object):
    """
    Cache decorator
    """
    # pylint: disable=too-few-public-methods

    # For dependency injection
    datetime = datetime

    def __init__(self, duration_provider=default_duration_provider):
        """
        Initialize the Cache object

        The cache can be intialized with a duration provider which is a
        callable returning the duration as a datetime.timedelta. This is done
        in order to be able to change the cache duration during runtime from
        configuration or for testing.

        The cache duration starts counting with the first call and does not
        depend on the arguments of the call.

        Args:
            duration_provider: Optional, defaults to four hours. A method
                returning a datetime.timedelta specifying the duration the
                cache is used until refreshed.
        """
        self._duration_provider = duration_provider
        self._expiration = None
        self._last_cached = None
        self._wrapped = None
        self._cache = {}

    def __call__(self, wrapped):
        """
        Wrap the original function

        Args:
            wrapped: The function to be wrapped.

        Returns:
            A function wrapping the original function and performing the
            caching.
        """
        self._wrapped = wrapped
        return CacheWrapper(self)

    def expire_cache(self):
        """
        Expire the cache
        """
        self._last_cached = None

    def wrapper(self, *args, **kwargs):
        """
        Cache the wrapped function
        """
        cache_key = self._hash(args, kwargs)
        cache_duration = self._duration_provider()
        now = self.datetime.now()

        is_cached = cache_key in self._cache
        is_expired = self._last_cached is None or \
            now > self._last_cached + cache_duration

        if is_cached and not is_expired:
            return self._cache[cache_key]
        else:
            cache_value = self._wrapped(*args, **kwargs)
            self._cache[cache_key] = cache_value
            self._last_cached = now
            return cache_value

    @classmethod
    def _hash(cls, args, kwargs):
        """
        Hash the args and kwargs passed to the function

        The arguments need to be cached in order to cache the value depending
        on those arguments.
        """
        values = []
        for arg in args:
            values.append(arg)
        for key in sorted(kwargs.keys()):
            values.append(key)
            values.append(kwargs[key])
        result_hash = hashlib.sha1()
        for value in values:
            result_hash.update(hashlib.sha1(repr(value)).digest())
        return result_hash.digest()

# pylint: disable=invalid-name
cached = Cache
