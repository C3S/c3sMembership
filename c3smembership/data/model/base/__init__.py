# -*- coding: utf-8  -*-
"""
Base package for all SqlAlchemy model packages.

Example::

    from base import Base

    class SomeModelClass(Base):
        pass
"""

from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)


# pylint: disable=invalid-name
Base = declarative_base()

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
