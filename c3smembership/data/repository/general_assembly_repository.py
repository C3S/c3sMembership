# -*- coding: utf-8  -*-
"""
Repository for accessing and operating with member data.
"""

from datetime import (
    datetime,
)

from sqlalchemy import (
    and_,
)
from sqlalchemy.sql import func

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.general_assembly import GeneralAssembly
from c3smembership.data.model.base.general_assembly_invitation import \
    GeneralAssemblyInvitation
from c3smembership.data.repository.member_repository import MemberRepository


class GeneralAssemblyRepository(object):
    """
    Repository for general assemblies.
    """

    datetime = datetime

    @classmethod
    def get_invitees(cls, general_assembly_number, invitees_count):
        """
        Gets a number of members which have not yet been invited to the general
        assembly.

        Queries the database for members, where:

        - members are members
        - members have not received their invitation email yet

        Args:
            general_assembly_number: Integer. The number of the general
                assembly for which the invitees are returned.
            invitees_count: Integer. Number of invitees returned at maximum.

        Returns:
            A list member objects.
        """
        # pylint: disable=no-member
        # In SqlAlchemy the True comparison must be done as "a == True" and not
        # in the python default way "a is True". Therefore:
        # pylint: disable=singleton-comparison
        return (
            # Get members
            DBSession.query(C3sMember)
            # combine with the general assembly requested as a cross join with
            # the one general assembly row
            .join(
                GeneralAssembly,
                GeneralAssembly.number == general_assembly_number)
            # combine them with invitations for this member to this general
            # assembly if any
            .outerjoin(
                GeneralAssemblyInvitation,
                and_(
                    C3sMember.id == GeneralAssemblyInvitation.member_id,
                    GeneralAssemblyInvitation.general_assembly_id ==
                    GeneralAssembly.id
                )
            )
            # but only
            .filter(
                and_(
                    # if no invitation has been sent
                    GeneralAssemblyInvitation.id == None,
                    # and the member has membership at the assmebly date
                    C3sMember.is_member_filter(GeneralAssembly.date),
                )
            )
            # get as many as requested
            .slice(0, invitees_count)
            # and get all of the actual records
            .all()
        )

    @classmethod
    def get_member_by_token(cls, token):
        """
        Find a member by token used for GA and BarCamp

        This is needed when a user returns from reading her email
        and clicking on a link containing the token.

        Returns:
            object: C3sMember object
        """
        # pylint: disable=no-member
        return (
            DBSession.query(C3sMember)
            .join(GeneralAssemblyInvitation)
            .filter(GeneralAssemblyInvitation.token == token)
            .first()
        )

    @classmethod
    def get_member_invitations(
            cls, membership_number, earliest=None, latest=None):
        """
        Get all general assembly invitations of the member

        Args:
            membership_number: The membership number of the member of which
                the general assembly invitations are returned.
            earliest: Optional. The earliest date for which general assemblies
                are returned.
            latest: Optional. The latest date for which general assemblies
                are returned.

        Returns:
            All general assemblies not earlier than earliest and not later than
            latest with number, name, date, invited flag, sent date and token.
        """
        # pylint: disable=no-member
        assembly_date_filter = True
        if earliest is not None:
            assembly_date_filter = and_(
                assembly_date_filter,
                GeneralAssembly.date >= earliest
            )
        if latest is not None:
            assembly_date_filter = and_(
                assembly_date_filter,
                GeneralAssembly.date <= latest
            )

        result = []
        assemblies = (
            # Get number, name and date of general assembly with invitation
            # sent date and token
            DBSession.query(
                GeneralAssembly.number,
                GeneralAssembly.name,
                GeneralAssembly.date,
                GeneralAssemblyInvitation.sent,
                GeneralAssemblyInvitation.token)
            .select_from(GeneralAssembly)
            # combine with the member as a cross join with the one member
            # requested
            .outerjoin(
                C3sMember,
                C3sMember.membership_number == membership_number
            )
            # combine with the invitations to for this member to the general
            # assemblies
            .outerjoin(
                GeneralAssemblyInvitation,
                and_(
                    GeneralAssemblyInvitation.member_id == C3sMember.id,
                    GeneralAssemblyInvitation.general_assembly_id ==
                    GeneralAssembly.id
                )
            )
            # filter for earliest and latest
            .filter(assembly_date_filter)
            # and get all of the actual records
            .all()
        )

        for assembly in assemblies:
            result.append({
                'number': assembly.number,
                'name': assembly.name,
                'date': assembly.date,
                'flag': (assembly.sent is not None),
                'sent': assembly.sent,
                'token': assembly.token,
            })
        return result

    @classmethod
    def get_member_invitation(cls, membership_number, general_assembly_number):
        """
        Get the invitation of the member for the general assembly

        Args:
            membership_number: String. The membership number of the member for
                which the invitation is returned.
            general_assembly_number: Integer. The number of the general
                assembly for which the member's invitation is returned.

        Returns:
            A general assembly invitation as a dictionary with properties
            number, name, date, flag and sent.
        """
        invitations = cls.get_member_invitations(membership_number)
        for invitation in invitations:
            if invitation['number'] == general_assembly_number:
                return invitation
        return None

    @classmethod
    def invite_member(cls, membership_number, general_assembly_number, token):
        """
        Store the member invitation for the general assembly

        Args:
            membership_number: Integer. The membership number of the member for
                which the general assembly invitation is stored.
            general_assembly_number: Integer. The number of the general
                assembly for which the invitation is stored for the member.
            token: String. The token set to verify the member for API access by
                the ticketing application.
        """
        # pylint: disable=no-member
        member = MemberRepository.get_member(membership_number)
        assembly = cls.get_general_assembly(general_assembly_number)
        invitation = GeneralAssemblyInvitation(
            assembly, member, cls.datetime.now(), token)
        DBSession.add(invitation)
        DBSession.flush()

    @classmethod
    def get_general_assemblies(cls):
        """
        Get general assemblies
        """
        # pylint: disable=no-member
        return DBSession \
            .query(GeneralAssembly) \
            .all()

    @classmethod
    def get_general_assembly(cls, number):
        """
        Get general assembly details
        """
        if not isinstance(number, int):
            raise ValueError('Number must be an integer.')
        # pylint: disable=no-member
        return DBSession \
            .query(GeneralAssembly) \
            .filter(GeneralAssembly.number == number) \
            .first()

    @classmethod
    def get_latest_general_assembly(cls):
        """
        Get details of the latest general assembly

        The latest general assembly is the one with the date later than all
        other general assembly dates.

        In case there are two general assemblies at the same ĺatest date an
        unpredictable one of them in returned depending on factors like
        creation date and implicit database ordering.
        """
        # pylint: disable=no-member
        latest_date = DBSession.query(func.max(GeneralAssembly.date)).scalar()
        return DBSession \
            .query(GeneralAssembly) \
            .filter(GeneralAssembly.date == latest_date) \
            .first()

    @classmethod
    def create_general_assembly(cls, number, name, date, invitation_subject_en,
                                invitation_text_en, invitation_subject_de,
                                invitation_text_de):
        """
        Create a general assembly

        Args:
            number: Integer. The number of the general assembly as a unique
                identifier.
            name: String. The name of the general assembly.
            date: `datetime.date`. The date at which the general assembly takes
                place.
            invitation_subject_en: String. The invitation subject sent to a
                member in English.
            invitation_text_en: String. The invitation text sent to a member
                in English.
            invitation_subject_de: String. The invitation subject sent to a
                member in German.
            invitation_text_de: String. The invitation text sent to a member
                in German.
        """
        assembly = GeneralAssembly(number, name, date, invitation_subject_en,
                                   invitation_text_en, invitation_subject_de,
                                   invitation_text_de)
        # pylint: disable=no-member
        DBSession.add(assembly)
        DBSession.flush()

    @classmethod
    def general_assembly_max_number(cls):
        """
        Get the maximum number assigned to a general assembly.
        """
        # pylint: disable=no-member
        return DBSession.query(func.max(GeneralAssembly.number)).scalar()

    @classmethod
    def edit_general_assembly(cls, number, name, date, invitation_subject_en,
                              invitation_text_en, invitation_subject_de,
                              invitation_text_de):
        """
        Edit a general assembly

        Args:
            number: Integer. The number of the general assembly to be edited.
            name: String. The edited name of the general assembly.
            date: `datetime.date`. The edited date at which the general
                assembly takes place.
            invitation_subject_en: String. The invitation subject sent to a
                member in English.
            invitation_text_en: String. The invitation text sent to a member
                in English.
            invitation_subject_de: String. The invitation subject sent to a
                member in German.
            invitation_text_de: String. The invitation text sent to a member
                in German.

        Raises:
            ValueError: In case the a general assembly with the number given
                does not exist.
        """
        assembly = cls.get_general_assembly(number)
        if assembly is None:
            raise ValueError(
                'A general assembly with this number does not exist.')
        assembly.name = name
        assembly.date = date
        assembly.invitation_subject_en = invitation_subject_en
        assembly.invitation_text_en = invitation_text_en
        assembly.invitation_subject_de = invitation_subject_de
        assembly.invitation_text_de = invitation_text_de
        # pylint: disable=no-member
        DBSession.flush()
