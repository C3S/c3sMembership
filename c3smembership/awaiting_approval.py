# -*- coding: utf-8 -*-
"""
When a membership applicant has both sent the signed form and transferred the
shares, the application is ready to be approved by the board of directors.

The information about members to be approved will be copied somewhere,
so the board can decide during one of its virtual meetings.
"""
from pyramid.view import view_config

from c3smembership import unicode
from c3smembership.models import (
    C3sMember,
)


@view_config(
    renderer='string',
    permission='manage',
    route_name='afms_awaiting_approval'
)
def afms_awaiting_approval(request):
    """
    List the applications for membership to be approved by the board.

    === ======================================
    URL http://app:port/afms_awaiting_approval
    === ======================================

    Returns:
        Multiline string for copy and paste (using Pyramids string_renderer).
    """

    afms = C3sMember.afms_ready_for_approval()

    # print("there are {} afms ready for approval".format(len(afms)))

    output_string = u"""\n"""
    # output_string = u"""there are {} afms ready for approval \n""".format(
    #    len(afms))

    if len(afms) > 0:
        output_string += u"""Neue Genossenschaftsmitglieder\n"""
        output_string += u"""------------------------------\n\n"""
        output_string += u"""Vorname      | Name       | Anteile | Typ \n"""
        output_string += u"""-----------  | ---------- | ------- | ----- \n"""

    for afm in afms:
        output_string += u"""{}      | {}     |   {}    | {} \n""".format(
            unicode(afm.firstname),
            unicode(afm.lastname),
            afm.num_shares,
            'legal entity/inv.' if afm.is_legalentity else afm.membership_type
        )

    # we can not see aufstockers as of now, or?
    output_string += u"""\nAufstocker\n"""
    output_string += u"""------------------------------\n\n"""
    output_string += u"""Vorname      | Name        | Anteile | Typ \n"""
    output_string += u"""-----------  | ----------  | ------- | ----- \n"""
    output_string += u"""\n TODO: check! \n"""
    return output_string
