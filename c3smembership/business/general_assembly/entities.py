# -*- coding: utf-8  -*-
"""
General assembly business entities
"""


class GeneralAssembly(object):
    """
    General assembly business entity
    """
    def __init__(self, number, name, date, invitation_subject_en,
                 invitation_text_en, invitation_subject_de,
                 invitation_text_de):
        """
        Initialise the general assembly business entity

        Args:
            number: Integer. The business key number of the general assembly.
            name: String. The name of the general assembly.
            date: Date. The date of the general assembly.
            invitation_subject_en: String. The invitation subject sent to a
                member in English.
            invitation_text_en: String. The invitation text sent to a member in
                English.
            invitation_subject_de: String. The invitation subject sent to a
                member in German.
            invitation_text_de: String. The invitation text sent to a member in
                German.
        """
        self.number = number
        self.name = name
        self.date = date
        self.invitation_subject_en = invitation_subject_en
        self.invitation_text_en = invitation_text_en
        self.invitation_subject_de = invitation_subject_de
        self.invitation_text_de = invitation_text_de


class GeneralAssemblyInvitation(object):
    """
    Invitation of a member to a general assembly

    The general assembly invitation describes an invitation for a member to a
    general assembly with sent timestamp and token string.
    """
    def __init__(self, general_assembly, member, sent, token=None):
        """
        Initialises the general assembly invitation business entity

        Args:
            general_assembly: GeneralAssembly. The general assembly for which
                the invitation was sent.
            member: C3SMember. The member to which the invitation was sent.
            sent: Datetime. Indicates the time at which the invitation to the
                general assembly was sent to the member
            token: Optional 255 character string. Can be used for validating
                the user's identity for example when used in a link to register
                at an event management application
        """
        self.general_assembly = general_assembly
        self.member = member
        self.sent = sent
        self.token = token
