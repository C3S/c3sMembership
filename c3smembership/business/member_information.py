# -*- coding: utf-8 -*-
"""
Provides member information.
"""


class MemberInformation(object):
    """
    Provides member information.
    """

    def __init__(self, member_repository):
        """
        Initialises the MemberInformation object.

        Args:
            member_repository: The member repository object used to access
                member data.
        """
        self._member_repository = member_repository

    def get_accepted_members_count(self, effective_date=None):
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
        return self._member_repository.get_accepted_members_count(
            effective_date)

    def get_accepted_members_sorted(self, effective_date=None):
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
        return self._member_repository.get_accepted_members_sorted(
            effective_date)

    def get_members_filtered(
            self, membership_type=None, membership_accepted=None,
            membership_loss_threshold=None):
        """
        Gets members filtered by membership type, membership acceptance and
        membership loss, sorted by lastname ascending and firstname ascending.

        Args:
            membership_type: Optional. A membership type like u'normal' or
                u'investing' to filter by. If None, all membership types are
                included.
            membership_accepted: Optional. If True, only members whose
                membership has been accepted are returned, if False only those
                whose membership has not been accepted. If None, both are
                included.
            membership_loss_threshold: Optional. A date. Members whose
                membership_loss_date lies before this date are excluded.
                Members without a membership loss date as well as members with
                a membership loss date on or after this date are included as
                their membership loss is not yet effective.

        Returns:
            All members matching the filter criteria sorted by lastname
            ascending and firstname ascending.
        """
        return self._member_repository.get_members_filtered(
            membership_type,
            membership_accepted,
            membership_loss_threshold)

    def get_member(self, membership_number):
        """
        Gets the member of the specified membership number.

        Args:
            membership_number: The membership number of the member which is
                returned.

        Returns:
            The membership of the specified membership number.
        """
        return self._member_repository.get_member(membership_number)

    def get_member_by_id(self, member_id):
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
        return self._member_repository.get_member_by_id(member_id)
