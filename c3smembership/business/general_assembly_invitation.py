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
