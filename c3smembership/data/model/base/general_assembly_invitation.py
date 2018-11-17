# -*- coding: utf-8  -*-
"""
General assembly invitation entity providing information about invitations to
general assemblies sent to members.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Unicode,
)
from sqlalchemy.orm import relationship

from c3smembership.data.model.base import Base
# pylint: disable=unused-import
# Import GeneralAssembly for the foreign key relationship
from c3smembership.data.model.base.general_assembly import GeneralAssembly


class GeneralAssemblyInvitation(Base):
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

    def __init__(self, general_assembly, member, sent, token=None):
        """
        Initialises the GeneralAssemblyInvitation object

        Args:
            general_assembly: GeneralAssembly. The general assembly for which
                the invitation was sent.
            member: C3SMember. The member to which the invitation was sent.
            sent: Datetime. Indicates the time at which the invitation to the
                general assembly was sent to the member
            token: Optional 255 character string. Can be used for validating
                the user's identity for example when used in a link to register
                at an event management application
        """
        self.general_assembly = general_assembly
        self.member = member
        self.sent = sent
        self.token = token
