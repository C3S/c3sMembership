# -*- coding: utf-8 -*-
"""
Test the c3smembership.cache module
"""

from datetime import (
    datetime,
    timedelta,
)
from unittest import TestCase

from mock import Mock

from c3smembership.cache import (
    Cache,
    cached,
    default_duration_provider,
)


class CacheTest(TestCase):
    """
    Test the Cache class
    """

    def setUp(self):
        self.dummy_duration_provider = Mock()
        self.function_mock = Mock()
        self.cache = Cache(duration_provider=self.dummy_duration_provider)
        self.cache.datetime = Mock()
        self.cached_function = self.cache(self.function_mock)

    def test_decorator(self):
        """
        Test the cached decorator
        """
        self.assertEqual(cached, Cache)

    def _init(self, now, duration, result):
        self.cache.datetime.now.side_effect = [now]
        self.dummy_duration_provider.side_effect = [duration]
        self.function_mock.side_effect = [result]

    def test_cache_caching(self):
        """
        Test the cache method for caching

        1. Call 1 is executed
        2. Call 1 again not expired gets from cache
        3. Call 2 is executed
        """
        # 1. Call 1 is executed
        self._init(
            datetime(2019, 5, 21, 20, 6, 10),
            timedelta(minutes=1),
            'function result 1')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.function_mock.assert_called_with(1, 'a,', None, True)
        self.assertEqual(result, 'function result 1')

        # 2. Call 1 again not expired gets from cache
        self._init(
            datetime(2019, 5, 21, 20, 7, 10),
            timedelta(minutes=1),
            'function result 2')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.assertEqual(result, 'function result 1')

        # 3. Call 2 is executed
        self._init(
            datetime(2019, 5, 21, 20, 6, 10),
            timedelta(minutes=1),
            'function result 3')

        result = self.cached_function(2, a='b,', flag=False)

        self.assertEqual(len(self.function_mock.mock_calls), 2)
        self.function_mock.assert_called_with(2, a='b,', flag=False)
        self.assertEqual(result, 'function result 3')

    def test_cache_time_expiration(self):
        """
        Test the cache method for time expiration

        1. Call 1 is executed
        2. Call 1 again expired is executed
        3. Call 1 again not expired gets from cache with newly cached value
        """
        # 1. Call 1 is executed
        self._init(
            datetime(2019, 5, 21, 20, 6, 10),
            timedelta(minutes=1),
            'function result 1')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.function_mock.assert_called_with(1, 'a,', None, True)
        self.assertEqual(result, 'function result 1')

        # 2. Call 1 again expired is executed
        self._init(
            datetime(2019, 5, 21, 21, 7, 11),
            timedelta(minutes=1),
            'function result 3')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 2)
        self.assertEqual(result, 'function result 3')

        # 3. Call 1 again not expired gets from cache with newly cached value
        self._init(
            datetime(2019, 5, 21, 21, 8, 11),
            timedelta(minutes=1),
            'whatever')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 2)
        self.assertEqual(result, 'function result 3')

    def test_cache_explicit_expiration(self):
        """
        Test the cache method for explicit expiration

        1. Call 1
        2. Call 1 again not expired after explicit expiration
        """
        # 1. Call 1
        self._init(
            datetime(2019, 5, 21, 21, 8, 11),
            timedelta(minutes=1),
            'before explicit expiration')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.assertEqual(result, 'before explicit expiration')

        # 2. Call 1 again not expired after explicit expiration
        self._init(
            datetime(2019, 5, 21, 21, 8, 11),
            timedelta(minutes=1),
            None)
        self.cached_function.expire_cache()
        self._init(
            datetime(2019, 5, 21, 21, 8, 11),
            timedelta(minutes=1),
            'after explicit expiration')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 2)
        self.assertEqual(result, 'after explicit expiration')

    def test_cache_duration_runtime(self):
        """
        Test the cache method for cache duration change during runtime

        1. Call 1
        2. Call 1 again which only expires due to new cache duration
        """
        # 1. Call 1
        self._init(
            datetime(2019, 5, 21, 21, 8, 11),
            timedelta(minutes=1),
            'some result')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.assertEqual(result, 'some result')

        # 2. Call 1 again which only expires due to new cache duration
        self._init(
            datetime(2019, 5, 21, 22, 8, 11),
            timedelta(hours=1),
            'something else')

        result = self.cached_function(1, 'a,', None, True)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.assertEqual(result, 'some result')

    def test_cache_kwargs(self):
        """
        Test the cache method for different kwargs orders

        1. Call 1
        2. Call 1 cached with kwargs differently ordered
        """
        # 1. Call 1
        self._init(
            datetime(2019, 5, 21, 20, 6, 10),
            timedelta(minutes=1),
            'function result 2')

        result = self.cached_function(2, a='b,', flag=False)

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.function_mock.assert_called_with(2, a='b,', flag=False)
        self.assertEqual(result, 'function result 2')

        # 2. Call 1 cached with kwargs differently ordered
        self._init(
            datetime(2019, 5, 21, 20, 6, 10),
            timedelta(minutes=1),
            'something new')

        result = self.cached_function(2, flag=False, a='b,')

        self.assertEqual(len(self.function_mock.mock_calls), 1)
        self.assertEqual(result, 'function result 2')

    def test_default_duration_provider(self):
        """
        Test the default_duration_provider method"
        """
        self.assertEqual(default_duration_provider(), timedelta(hours=4))
