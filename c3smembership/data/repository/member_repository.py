# -*- coding: utf-8  -*-
"""
Repository for accessing and operating with member data.
"""

from sqlalchemy.sql import func
from sqlalchemy import (
    and_,
    not_,
)
from datetime import date

from c3smembership.data.model.base import DBSession
from c3smembership.models import C3sMember


class MemberRepository(object):
    """
    Repository for members.
    """

    @classmethod
    def get_member(cls, membership_number):
        """
        Gets the member of the specified membership number.

        Args:
            membership_number: The membership number of the member which is
                returned.

        Returns:
            The membership of the specified membership number.
        """
        # pylint: disable=no-member
        return DBSession.query(C3sMember).filter(
            C3sMember.membership_number == membership_number).first()

    @classmethod
    def get_member_by_id(cls, member_id):
        """
        Gets the member of the specified member ID.

        TODO: The member ID is a database internal ID and must not be exposed
        from the data layer. Therefore, the implementation must be adjusted to
        use the get_member method using the membership number.

        Args:
            member_id: The technical ID of the member which is returned.

        Returns:
            The membership of the specified member id.
        """
        # pylint: disable=no-member
        return DBSession.query(C3sMember).filter(
            C3sMember.id == member_id).first()

    @classmethod
    def get_accepted_members(cls, effective_date=None):
        """
        Gets all members which have been accepted until and including the
        specified effective date.

        Args:
            effective_date: Optional. The date on which the membership has been
                accepted. If not specified system date is used as effective
                date.

        Returns:
            All members which have been accepted until and including the
            specified effective date.
        """
        return cls._members_query(effective_date).all()

    @classmethod
    def get_accepted_members_sorted(cls, effective_date=None):
        """
        Gets all members which have been accepted until and including the
        specified effective date sorted by lastname ascending and firstname
        ascending.

        Args:
            effective_date: Optional. The date on which the membership has been
                accepted. If not specified system date is used as effective
                date.

        Returns:
            All members which have been accepted until and including the
            specified effective date sorted by lastname ascending and firstname
            ascending.
        """
        return cls._members_query(effective_date).order_by(
            C3sMember.lastname.asc(),
            C3sMember.firstname.asc()).all()

    @classmethod
    def _members_query(cls, effective_date=None):
        """
        Gets the query to retrieve members accepted until and including the
        specified effective date.

        Args:
            effective_date: Optional. The date on which the membership has been
                accepted. If not specified system date is used as effective
                date.

        Returns:
            The query to retrieve members accepted until and including the
            specified effective date.
        """
        # pylint: disable=no-member
        return DBSession.query(C3sMember) \
            .filter(cls._is_member_filter(effective_date))

    @classmethod
    def get_accepted_members_count(cls, effective_date=None):
        """
        Gets the number of members which have been accpeted until and including
        the specified effective date.

        Args:
            effective_date: Optional. The date on which the membership has been
                accepted. If not specified system date is used as effective
                date.

        Returns:
            The number of members which have been accpeted until and including
            the specified effective date.
        """
        # pylint: disable=no-member
        return DBSession.query(func.count(C3sMember.id)) \
            .filter(cls._is_member_filter(effective_date)) \
            .scalar()

    @classmethod
    def _membership_lost_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which lost
        membership before the specified effective date.

        Args:
            effective_date: Optional. The date before which the membership was
                lost. If not specified then the current date of is used.

        Returns:
            A filter only matching entities which lost membership before the
            specified effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            C3sMember.membership_loss_date != None,
            C3sMember.membership_loss_date < effective_date)

    @classmethod
    def _membership_accepted_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which had their
        membership accepted before or on the specified effective date.

        Args:
            effective_date: Optional. The date before or on which the
                membership was accepted. If not specified then the current date
                of is used.

        Returns:
            A filter only matching entities which had their membership accepted
            before or on the specified effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            C3sMember.membership_accepted,
            C3sMember.membership_date != None,
            C3sMember.membership_date <= effective_date)

    @classmethod
    def _is_member_filter(cls, effective_date=None):
        """
        Provides a SqlAlchemy filter only matching entities which are members
        at the specified effective date.

        For being a member the membership must have been accepted and the
        membership must not have been lost.

        Args:
            effective_date: Optional. The date for which the membership status
                is checked. If not specified then the current date of is used.

        Returns:
            A filter matching all entities which are members as the specified
            effective date.
        """
        if effective_date is None:
            effective_date = date.today()
        return and_(
            cls._membership_accepted_filter(effective_date),
            not_(cls._membership_lost_filter(effective_date)))
