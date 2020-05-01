# -*- coding: utf-8  -*-
"""
General assembly data entities
"""

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
)
from sqlalchemy.orm import relationship

from c3smembership.data.model.base import Base

from c3smembership.business.general_assembly.entities import GeneralAssembly \
    as GeneralAssemblyBusinessEntity
from c3smembership.business.general_assembly.entities import \
    GeneralAssemblyInvitation as GeneralAssemblyInvitationBE


class GeneralAssembly(GeneralAssemblyBusinessEntity, Base):
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

    @classmethod
    def create_from_business_entity(cls, general_assembly):
        """
        Create a general assembly data entity from a general assembly business
        entity

        Args:
            general_assembly: The general assembly business entity used to
                create the data entity.
        """
        return cls(general_assembly.number, general_assembly.name,
                   general_assembly.date,
                   general_assembly.invitation_subject_en,
                   general_assembly.invitation_text_en,
                   general_assembly.invitation_subject_de,
                   general_assembly.invitation_text_de)

    def update_from_business_entity(self, general_assembly):
        """
        Update the general assembly data entity from a general assembly
        business entity

        Args:
            general_assembly: The general assembly business entity used to
                update the data entity.
        """
        self.name = general_assembly.name
        self.date = general_assembly.date
        self.invitation_subject_en = general_assembly.invitation_subject_en
        self.invitation_text_en = general_assembly.invitation_text_en
        self.invitation_subject_de = general_assembly.invitation_subject_de
        self.invitation_text_de = general_assembly.invitation_text_de


class GeneralAssemblyInvitation(GeneralAssemblyInvitationBE, Base):
    """
    Invitation of a member to a general assembly

    The general assembly invitation stores an invitation for a member to a
    general assembly with sent timestamp and token string.
    """
    # pylint: disable=too-few-public-methods
    __tablename__ = 'GeneralAssemblyInvitation'

    # pylint: disable=invalid-name
    # primary key
    id = Column(Integer, primary_key=True)

    # foreign keys
    general_assembly_id = Column(Integer, ForeignKey('GeneralAssembly.id'))
    member_id = Column(Integer, ForeignKey('members.id'))

    # relationships
    general_assembly = relationship('GeneralAssembly')
    member = relationship('C3sMember')

    # properties
    sent = Column(DateTime(), nullable=False)
    token = Column(Unicode(255))
