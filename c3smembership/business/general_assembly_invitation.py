# -*- coding: utf-8 -*-
"""
General assembly invitations.
"""

from datetime import date


class GeneralAssemblyInvitation(object):

    date = date

    def __init__(self, general_assembly_repository):
        self._general_assembly_repository = general_assembly_repository

    def get_member_invitations(self, member):
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
