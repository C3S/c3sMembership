# -*- coding: utf-8 -*-
"""
General assembly invitations.
"""

from datetime import date


class GeneralAssemblyInvitation(object):
    """
    Handle general assembly invitation business logic
    """

    date = date

    def __init__(self, general_assembly_repository):
        """
        Initialize the GeneralAssemblyInvitation object

        Args:
            general_assembly_repository: The GeneralAssemblyRepository class.
        """
        self._general_assembly_repository = general_assembly_repository

    def get_member_invitations(self, member):
        """
        Get member invitations

        Lists all general assemblies for which apply to a member, whether
        the member was invited and whether they can be invited.

        Args:
            member: The member for which the general assembly invitations are
                returned.

        Returns:
            A dictionary with the elements:

            - 'number': An integer representing the number of the general
              assembly.
            - 'name': A string representing the name of the general assembly.
            - 'date': A date representing the date of the general assembly.
            - 'flag': A boolean indication whether or not the member has been
              invited.
            - 'can_invite': A boolean indicating whether an invitation for the
              general assembly can be sent to the member.
        """
        general_assembly_invitations = self._general_assembly_repository \
            .get_member_invitations(
                member.membership_number,
                member.membership_date,
                member.membership_loss_date)
        for general_assembly_invitation in general_assembly_invitations:
            # only invite if
            general_assembly_invitation['can_invite'] = (
                # not invited yet and
                not general_assembly_invitation['flag'] and
                # assembly in the future
                general_assembly_invitation['date'] >= self.date.today())

        return general_assembly_invitations

    def invite_member(self, member, general_assembly, token):
        """
        Invite member to general assembly

        Args:
            member: The member to invite to the general assembly.
            general_assembly: The general assembly the member is invited to.

        Raises:
            ValueError: In case the general assembly is in the past.
            ValueError: In case the member is not eligible to be invited to
                the general assembly.
            ValueError: In case the member has already been invited to the
                general assembly.
        """
        if general_assembly.date < self.date.today():
            raise ValueError(
                'The general assembly occurred in the past.')

        if not member.is_member(general_assembly.date):
            raise ValueError(
                'The member is not eligible to be invited to the general '
                'assembly')

        invitation = self._general_assembly_repository \
            .get_member_invitation(
                member.membership_number,
                general_assembly.number)
        if invitation is not None and invitation['flag']:
            raise ValueError(
                'The member has already been invited to the general assembly.')

        self._general_assembly_repository.invite_member(
            member.membership_number,
            general_assembly.number,
            token,
        )

    def get_general_assemblies(self):
        """
        Get all general assemblies
        """
        return self._general_assembly_repository.get_general_assemblies()
