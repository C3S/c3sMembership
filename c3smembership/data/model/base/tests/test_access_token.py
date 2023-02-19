# -*- coding: utf-8 -*-
"""
"""

from unittest import TestCase
from c3smembership.data.model.base.access_token import AccessToken
import datetime


class DateTimeMock(object):

    def __init__(self, value):
        self._value = value

    def set(self, value):
        self._value = value

    def now(self):
        return self._value


class AccessTokenTest(TestCase):

    def test_init(self):
        datetime_mock = DateTimeMock(datetime.datetime(2000, 1, 1, 0, 0, 0))
        AccessToken.datetime = datetime_mock
        token = AccessToken()
        self.assertEqual(len(token.token), AccessToken.LENGTH)
        self.assertEqual(
            token.creation, datetime.datetime(2000, 1, 1, 0, 0, 0))
        self.assertEqual(token.expiration,
                         datetime.datetime(2000, 1, 15, 0, 0, 0))
        self.assertFalse(token.is_expired)
        datetime_mock.set(datetime.datetime(2000, 1, 14, 23, 59, 59))
        self.assertFalse(token.is_expired)
        datetime_mock.set(datetime.datetime(2000, 1, 15, 0, 0, 0))
        self.assertTrue(token.is_expired)
        datetime_mock.set(datetime.datetime(2000, 1, 15, 0, 0, 1))
        self.assertTrue(token.is_expired)

    def test_init_parameters(self):
        datetime_mock = DateTimeMock(datetime.datetime(2000, 1, 1, 0, 0, 0))
        AccessToken.datetime = datetime_mock
        token = AccessToken(
            available_characters='a',
            length=10,
            expiration_timespan=datetime.timedelta(days=1))
        self.assertEqual(token.token, 'aaaaaaaaaa')
        self.assertEqual(
            token.creation, datetime.datetime(2000, 1, 1, 0, 0, 0))
        self.assertEqual(token.expiration,
                         datetime.datetime(2000, 1, 2, 0, 0, 0))

    def test_exceptions(self):
        with self.assertRaises(TypeError):
            AccessToken(available_characters=3)
        with self.assertRaises(TypeError):
            AccessToken(available_characters='')
        with self.assertRaises(TypeError):
            AccessToken(length='')
        with self.assertRaises(TypeError):
            AccessToken(length=0)
        with self.assertRaises(TypeError):
            AccessToken(length=AccessToken.LENGTH + 1)
        with self.assertRaises(TypeError):
            AccessToken(expiration_timespan=3)
