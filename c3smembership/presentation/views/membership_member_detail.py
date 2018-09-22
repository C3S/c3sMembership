# -*- coding: utf-8 -*-
"""
Provide member detail information
"""

import logging

from datetime import date
from decimal import Decimal

from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice

LOG = logging.getLogger(__name__)


def get_member_details(request, member):
    """
    Gets the member details.
    """
    shares = request.registry.share_information.get_member_shares(
        member.membership_number)
    invoices15 = Dues15Invoice.get_by_membership_no(member.membership_number)
    invoices16 = Dues16Invoice.get_by_membership_no(member.membership_number)
    invoices17 = Dues17Invoice.get_by_membership_no(member.membership_number)
    invoices18 = Dues18Invoice.get_by_membership_no(member.membership_number)
    general_assembly_invitations = sorted(
        request.registry.general_assembly_invitation.get_member_invitations(
            member),
        key=lambda ga: ga['date'],
        reverse=True)

    return {
        'date': date,
        'D': Decimal,
        'member': member,
        'shares': shares,
        'invoices15': invoices15,
        'invoices16': invoices16,
        'invoices17': invoices17,
        'invoices18': invoices18,
        'general_assembly_invitations': general_assembly_invitations,
    }


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_detail.pt',
    permission='manage',
    route_name='member_details')
def member_details(request):
    """
    This view lets accountants view member details:

    - has their signature arrived?
    - how about the payment?

    Mostly all the info about an application or membership
    in the database can be seen here.
    """
    logged_in = authenticated_userid(request)
    membership_number = request.matchdict['membership_number']
    LOG.info(
        'member details of membership number %s checked by %s',
        membership_number,
        logged_in)

    member_information = request.registry.member_information
    member = member_information.get_member(membership_number)

    if member is None:
        request.session.flash(
            "A Member with id "
            "{} could not be found in the DB. run for the backups!".format(
                membership_number),
            'danger'
        )
        return HTTPFound(  # back to base
            request.route_url('toolbox'))

    return get_member_details(request, member)


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_detail.pt',
    permission='manage',
    route_name='detail')
def member_detail(request):
    """
    This view lets accountants view member details:

    - has their signature arrived?
    - how about the payment?

    Mostly all the info about an application or membership
    in the database can be seen here.
    """
    logged_in = authenticated_userid(request)
    memberid = request.matchdict['memberid']
    LOG.info("member details of id %s checked by %s", memberid, logged_in)

    member = C3sMember.get_by_id(memberid)

    if member is None:  # that memberid did not produce good results
        request.session.flash(
            "A Member with id "
            "{} could not be found in the DB. run for the backups!".format(
                memberid),
            'danger'
        )
        return HTTPFound(  # back to base
            request.route_url('toolbox'))

    return get_member_details(request, member)
