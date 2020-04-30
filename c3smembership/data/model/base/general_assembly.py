# -*- coding: utf-8  -*-
"""
General assembly data entity
"""

from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    Date,
)

from c3smembership.data.model.base import Base


class GeneralAssembly(Base):
    """
    General assembly data entity
    """
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
    invitation_subject_en = Column(Unicode(1000))
    """The invitation subject sent to a member in English."""
    invitation_text_en = Column(Unicode(1000000))
    """The invitation text sent to a member in English."""
    invitation_subject_de = Column(Unicode(1000))
    """The invitation subject sent to a member in German."""
    invitation_text_de = Column(Unicode(1000000))
    """The invitation text sent to a member in German."""

    def __init__(self, number, name, date, invitation_subject_en,
                 invitation_text_en, invitation_subject_de,
                 invitation_text_de):
        """
        Initialise the GeneralAssembly instance

        Args:
            number: Integer. The business key number of the general assembly.
            name: String. The name of the general assembly.
            date: Date. The date of the general assembly.
            invitation_subject_en: String. The invitation subject sent to a
                member in English.
            invitation_text_en: String. The invitation text sent to a member in
                English.
            invitation_subject_de: String. The invitation subject sent to a
                member in German.
            invitation_text_de: String. The invitation text sent to a member in
                German.
        """
        self.number = number
        self.name = name
        self.date = date
        self.invitation_subject_en = invitation_subject_en
        self.invitation_text_en = invitation_text_en
        self.invitation_subject_de = invitation_subject_de
        self.invitation_text_de = invitation_text_de
