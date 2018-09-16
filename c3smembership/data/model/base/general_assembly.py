# -*- coding: utf-8  -*-

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    Date,
)

from c3smembership.data.model.base import Base


class GeneralAssembly(Base):
    __tablename__ = 'GeneralAssembly'

    # primary key
    id = Column(Integer(), primary_key=True)
    """The database primary key id of the general assembly record."""

    # foreign keys
    number = Column(Integer())
    """The business key number of the general assembly."""
    name = Column(Unicode(255))
    """The name of the general assembly."""
    date = Column(Date())
    """The date of the general assembly."""

    def __init__(self, number, name, date):
        """
        Initialise the GeneralAssembly instance

        Args:
            number: Integer. The business key number of the general assembly.
            name: String. The name of the general assembly.
            date: Date. The date of the general assembly.
        """
        self.number = number
        self.name = name
        self.date = date
