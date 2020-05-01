# -*- coding: utf-8 -*-
"""
General assembly invitations.
"""

from datetime import date

from c3smembership.business.general_assembly.entities import GeneralAssembly


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

    def create_general_assembly(self, name, assembly_date,
                                invitation_subject_en, invitation_text_en,
                                invitation_subject_de, invitation_text_de):
        """
        Create a general assembly

        The general assembly must not be in the past. It can take place today
        or in the future

        Business rules:

        - The general assembly must be given a name.
        - The general assembly must take place in the future. The earliest
          possible date is tomorrow.

        Args:
            name: String. The name of the general assembly.
            assembly_date: `datetime.date`. The date at which the general
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
            ValueError: In case the general assembly is not given name
            ValueError: In case date is in the past
        """
        self._validate_general_assembly(name, assembly_date)
        general_assembly = GeneralAssembly(
            self.get_next_number(), name, assembly_date, invitation_subject_en,
            invitation_text_en, invitation_subject_de, invitation_text_de)
        self._general_assembly_repository.add_general_assembly(
            general_assembly)

    def edit_general_assembly(self, number, name, assembly_date,
                              invitation_subject_en, invitation_text_en,
                              invitation_subject_de, invitation_text_de):
        """
        Edit a general assembly

        The general assembly must not be in the past. It can take place today
        or in the future.

        Business rules:

        - The general assembly must be given a name.
        - The general assembly must take place in the future. The earliest
          possible date is tomorrow.

        Args:
            number: Integer. The number of the general assembly to be edited.
            name: String. The edited name of the general assembly.
            assembly_date: `datetime.date`. The edited date at which the
                general assembly takes place.
            invitation_subject_en: String. The invitation subject sent to a
                member in English.
            invitation_text_en: String. The invitation text sent to a member
                in English.
            invitation_subject_de: String. The invitation subject sent to a
                member in German.
            invitation_text_de: String. The invitation text sent to a member
                in German.

        Raises:
            ValueError: In case the general assembly is not given name
            ValueError: In case date is in the past
        """
        self._validate_general_assembly(name, assembly_date)
        assembly = self._general_assembly_repository.get_general_assembly(
            number)
        if assembly is None:
            raise ValueError('The general assembly does not exist.')
        general_assembly = GeneralAssembly(number, name, assembly_date,
                                           invitation_subject_en,
                                           invitation_text_en,
                                           invitation_subject_de,
                                           invitation_text_de)
        self._general_assembly_repository.edit_general_assembly(
            general_assembly)

    def _validate_general_assembly(self, name, assembly_date):
        """
        Validate the general assembly details

        Raises:
            ValueError: In case the general assembly is not given name
            ValueError: In case date is in the past
        """
        if not name:
            raise ValueError('The general assembly must be given a name.')
        if assembly_date < self.date.today():
            raise ValueError(
                'The general assembly must take place in the future.')

    def get_general_assembly(self, number):
        """
        Get all general assemblies
        """
        return self._general_assembly_repository.get_general_assembly(number)

    def get_general_assemblies(self):
        """
        Get all general assemblies
        """
        return self._general_assembly_repository.get_general_assemblies()

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
            raise ValueError('The general assembly occurred in the past.')

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

    def get_member_invitation(self, member, general_assembly_number):
        """
        Get the invitation of the member for the general assembly

        Args:
            membership_number: String. The membership number of the member for
                which the invitation is returned.
            general_assembly_number: Integer. The number of the general
                assembly for which the member's invitation is returned.

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

            None, if the general assembly does not apply to the member, e.g.
            because the membership period does not cover the general assembly
            date.
        """
        invitations = self.get_member_invitations(member)
        for invitation in invitations:
            if invitation['number'] == general_assembly_number:
                return invitation

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
                # assembly is not in the past
                general_assembly_invitation['date'] >= self.date.today())

        return general_assembly_invitations

    def get_next_number(self):
        """
        Get the next general assembly number

        The general assembly number uniquely identifies the general assembly.
        This method gets the number which is assigned to the next general
        assembly created.
        """
        max_number = self._general_assembly_repository \
            .general_assembly_max_number()
        if max_number is None:
            max_number = 0
        return (max_number + 1)

    def get_latest_general_assembly(self):
        """
        Get details of the latest general assembly

        The latest general assembly is the one with the date later than all
        other general assembly dates.

        In case there are two general assemblies at the same ĺatest date an
        unpredictable one of them in returned depending on factors like
        creation date and implicit database ordering.
        """
        return self._general_assembly_repository.get_latest_general_assembly()
