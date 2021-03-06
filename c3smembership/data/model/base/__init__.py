# -*- coding: utf-8  -*-
"""
Base package for all SqlAlchemy model packages.

Example::

    from base import Base

    class SomeModelClass(Base):
        pass
"""

from decimal import Decimal

import bcrypt
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
import sqlalchemy.types as types
from zope.sqlalchemy import register


# pylint: disable=invalid-name
Base = declarative_base()


DBSession = scoped_session(sessionmaker(autoflush=True))
register(DBSession)


def hash_password(password):
    """
    Calculates the password hash.
    """
    return bcrypt \
        .hashpw(password.encode('utf-8'), bcrypt.gensalt()) \
        .decode('utf-8')


def check_password(hashed_password, plain_password):
    """
    Checks the plain password against the hashed password.

    Args:
        hashed_password: The hash password created by using the hash_password
            method.
        plain_passwort: The plain password to compare with the hashed password.

    Returns:
        Boolean indicating whether the plain password matches the hashed
        password.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8'))


# TODO: Use standard SQLAlchemy Decimal when a database is used which supports
# it.
class SqliteDecimal(types.TypeDecorator):
    """
    Type decorator for persisting Decimal (currency values)

    TODO: Use standard SQLAlchemy Decimal
    when a database is used which supports it.
    """
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        else:
            return None

    def process_result_value(self, value, dialect):
        if value is not None and value != '':
            return Decimal(value)
        else:
            return None


DatabaseDecimal = SqliteDecimal
