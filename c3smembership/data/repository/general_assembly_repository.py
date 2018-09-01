# -*- coding: utf-8  -*-
"""
Repository for accessing and operating with member data.
"""

from sqlalchemy import (
    and_,
    or_,
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember


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
        return DBSession.query(C3sMember).filter(
            C3sMember.email_invite_token_bcgv18 == token).first()
