# -*- coding: utf-8  -*-
"""
Repository for accessing and operating with member data.
"""

from datetime import (
    date,
    datetime,
)

from sqlalchemy import (
    and_,
    or_,
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.member_repository import MemberRepository


GENERAL_ASSEMBLIES = [
    {
        'number': '1',
        'name': '1. ordentliche Generalversammlung',
        'date': date(2014, 8, 23),
    },
    {
        'number': '2',
        'name': '2. ordentliche Generalversammlung',
        'date': date(2015, 6, 13),
    },
    {
        'number': '3',
        'name': '3. ordentliche Generalversammlung',
        'date': date(2016, 4, 17),
    },
    {
        'number': '4',
        'name': '4. ordentliche Generalversammlung',
        'date': date(2017, 4, 2),
    },
    {
        'number': '5',
        'name': '5. ordentliche Generalversammlung',
        'date': date(2018, 6, 3),
    },
]


class GeneralAssemblyRepository(object):
    """
    Repository for general assemblies.
    """

    @classmethod
    def get_invitees(cls, num):
        """
        Get a given number *n* of members to invite for barcamp and GV.

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
        Find a member by token used for GA and BarCamp.

        This is needed when a user returns from reading her email
        and clicking on a link containing the token.

        Returns:
            object: C3sMember object
        """
        # pylint: disable=no-member
        return DBSession.query(C3sMember).filter(
            C3sMember.email_invite_token_bcgv18 == token).first()

    @classmethod
    def get_member_invitations(cls, membership_number):
        """
        Get all general assembly invitations of the member.

        Args:
            membership_number: The membership number of the member of which
                the general assembly invitations are returned.

        Returns:
            All general assemblies with number, name, date, invited flag and
            sent date to which the member could have been invited according to
            their membership status.
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
        # pylint: disable=consider-using-enumerate
        for i in range(len(GENERAL_ASSEMBLIES)):
            if member.is_member(GENERAL_ASSEMBLIES[i]['date']):
                result.append({
                    'number': GENERAL_ASSEMBLIES[i]['number'],
                    'name': GENERAL_ASSEMBLIES[i]['name'],
                    'date': GENERAL_ASSEMBLIES[i]['date'],
                    'flag': flags[i],
                    'sent': sent[i],
                    })
        return result

    @classmethod
    def get_member_invitation(cls, membership_number, general_assembly_number):
        invitations = cls.get_member_invitations(membership_number)
        for invitation in invitations:
            if invitation['number'] == general_assembly_number:
                return invitation

    @classmethod
    def invite_member(cls, membership_number, general_assembly_number, token):
        member = MemberRepository.get_member(membership_number)
        if general_assembly_number == '1':
            member.email_invite_date_bcgv14 = datetime.now()
            member.email_invite_flag_bcgv14 = True
        if general_assembly_number == '2':
            member.email_invite_date_bcgv15 = datetime.now()
            member.email_invite_flag_bcgv15 = True
            member.email_invite_token_bcgv15 = token
        if general_assembly_number == '3':
            member.email_invite_date_bcgv16 = datetime.now()
            member.email_invite_flag_bcgv16 = True
            member.email_invite_token_bcgv16 = token
        if general_assembly_number == '4':
            member.email_invite_date_bcgv17 = datetime.now()
            member.email_invite_flag_bcgv17 = True
            member.email_invite_token_bcgv17 = token
        if general_assembly_number == '5':
            member.email_invite_date_bcgv18 = datetime.now()
            member.email_invite_flag_bcgv18 = True
            member.email_invite_token_bcgv18 = token
