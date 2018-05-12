# -*- coding: utf-8  -*-
"""
Provides the base functionality for access tokens.
"""

# standard import
import datetime
import random

# external import
from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    DateTime,
)

# internal import
from c3smembership.data.model.base import Base


class AccessToken(Base):
    # pylint: disable=too-few-public-methods
    """
    An access token is a random string which can be used to authenticate a user
    for a specific action.

    The default set of characters includes upper and lower case characters as
    well as digits except for the similar looking signs i, I, 1, o, O and 0.

    As the default and maximum length for tokens is 24 characters the entropy
    of these tokens is:

        len(CHARACTERS) ^ LENGTH = 56 ^ 44 ≈ 8.32e76 ≈ 255 bit

    The default expiration time is 14 days.
    """

    # CONSTANTS
    CHARACTERS = u'abcdefghjklmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    LENGTH = 44  # Changing the length changes the data model!
    EXPIRATION_DAYS = 14

    # Keep local for test injection
    timedelta = datetime.timedelta
    datetime = datetime.datetime

    # Metadata
    __tablename__ = 'AccessToken'

    # Keys
    id = Column(Integer, primary_key=True)  # pylint: disable=invalid-name

    # Inheritance
    access_token_type = Column('access_token_type', Unicode(32))
    __mapper_args__ = {'polymorphic_on': access_token_type}

    # Properties
    token = Column(Unicode(LENGTH), nullable=False)
    creation = Column(DateTime(), nullable=False)
    expiration = Column(DateTime(), nullable=False)

    def __init__(
            self,
            available_characters=CHARACTERS,
            length=LENGTH,
            expiration_timespan=timedelta(days=EXPIRATION_DAYS)):
        """
        Initialises the AccessToken instance.

        Args:
            available_characters (unicode): A string of characters from which
                the random token is generated. The minimum length is one.
            length (int): The length of the random token to be generated.
            expiration_timespan (datetime.timedelta): The timespan for which
                the token is valid.

        Raises:
            TypeError:
                If available_characters does not contain at least one
                character.
                If length is not of type int.
                If length is smaller than one or larger than
                AccessToken.LENGTH.
                If expiration_timespan is not of type timedelta.
        """
        if len(available_characters) < 1:
            raise TypeError(
                'Parameter available_characters must contain at least one '
                'character.')
        if not isinstance(length, int):
            raise TypeError('Parameter length must be of type int.')
        if length < 1 or length > self.LENGTH:
            raise TypeError(
                'Parameter length must be at least one and at most ' +
                str(self.LENGTH))
        if not isinstance(expiration_timespan, self.timedelta):
            raise TypeError(
                'Parameter expiration_timespan must be of type timedelta.')

        self.token = self._generate_token(available_characters, length)
        now = self.datetime.now()
        self.creation = now
        self.expiration = now + expiration_timespan

    @classmethod
    def _generate_token(cls, available_characters, length):
        """
        Generates a token from a list of available characters and a given
        length.

        Args:
            available_characters (string): A string of characters from which
                the random token is generated.
            length (int): The length of the random token to be generated.

        Returns:
            A random string token with the specified length chosen from the
            list of available characters.
        """
        return u''.join(
            random.choice(
                available_characters
            ) for x in range(length))

    @property
    def is_expired(self):
        """
        Indicates whether the token is expired according to its expiration
        date.
        """
        return self.datetime.now() >= self.expiration
