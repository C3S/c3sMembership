# -*- coding: utf-8  -*-
"""
Repository for accessing and operating with member data.
"""

from datetime import (
    datetime,
)

from sqlalchemy import (
    and_,
    or_,
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.general_assembly import GeneralAssembly
from c3smembership.data.repository.member_repository import MemberRepository


class GeneralAssemblyRepository(object):
    """
    Repository for general assemblies.
    """

    @classmethod
    def get_invitees(cls, num):
        """
        Get a given number *n* of members to invite for barcamp and GV

        Queries the database for members, where

        * members are accepted
        * members have not received their invitation email yet

        Args:
          num is the number *n* of invitees to return

        Returns:
          a list of *n* member objects
        """
        # pylint: disable=no-member
        return DBSession.query(C3sMember).filter(
            and_(
                C3sMember.is_member_filter(),
                or_(
                    (C3sMember.email_invite_flag_bcgv18 == 0),
                    (C3sMember.email_invite_flag_bcgv18 == ''),
                    # pylint: disable=singleton-comparison
                    (C3sMember.email_invite_flag_bcgv18 == None),
                )
            )
        ).slice(0, num).all()

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
        return DBSession.query(C3sMember).filter(
            C3sMember.email_invite_token_bcgv18 == token).first()

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
            latest with number, name, date, invited flag and sent date.
        """
        result = []
        member = MemberRepository.get_member(membership_number)
        flags = [
            member.email_invite_flag_bcgv14,
            member.email_invite_flag_bcgv15,
            member.email_invite_flag_bcgv16,
            member.email_invite_flag_bcgv17,
            member.email_invite_flag_bcgv18,
        ]
        sent = [
            member.email_invite_date_bcgv14,
            member.email_invite_date_bcgv15,
            member.email_invite_date_bcgv16,
            member.email_invite_date_bcgv17,
            member.email_invite_date_bcgv18,
        ]
        # pylint: disable=no-member
        general_assemblies = DBSession \
            .query(GeneralAssembly) \
            .order_by(GeneralAssembly.number) \
            .all()
        # pylint: disable=consider-using-enumerate,invalid-name
        for i in range(len(general_assemblies)):
            is_later_than_or_equal_to_earliest = \
                earliest is None \
                or \
                earliest <= general_assemblies[i].date
            is_earlier_than_or_equal_to_latest = \
                latest is None \
                or \
                latest >= general_assemblies[i].date
            if is_later_than_or_equal_to_earliest and \
                    is_earlier_than_or_equal_to_latest:
                result.append({
                    'number': general_assemblies[i].number,
                    'name': general_assemblies[i].name,
                    'date': general_assemblies[i].date,
                    'flag': flags[i],
                    'sent': sent[i],
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
        member = MemberRepository.get_member(membership_number)
        if general_assembly_number == 1:
            member.email_invite_date_bcgv14 = datetime.now()
            member.email_invite_flag_bcgv14 = True
        if general_assembly_number == 2:
            member.email_invite_date_bcgv15 = datetime.now()
            member.email_invite_flag_bcgv15 = True
            member.email_invite_token_bcgv15 = token
        if general_assembly_number == 3:
            member.email_invite_date_bcgv16 = datetime.now()
            member.email_invite_flag_bcgv16 = True
            member.email_invite_token_bcgv16 = token
        if general_assembly_number == 4:
            member.email_invite_date_bcgv17 = datetime.now()
            member.email_invite_flag_bcgv17 = True
            member.email_invite_token_bcgv17 = token
        if general_assembly_number == 5:
            member.email_invite_date_bcgv18 = datetime.now()
            member.email_invite_flag_bcgv18 = True
            member.email_invite_token_bcgv18 = token

    @classmethod
    def get_general_assemblies(cls):
        """
        Get general assemblies
        """
        return DBSession \
            .query(GeneralAssembly) \
            .all()
