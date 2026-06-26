# -*- coding: utf-8 -*-
"""
Provide member detail information
"""

import logging

from datetime import date
from decimal import Decimal

from pyramid.view import view_config

from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.presentation.schemas.member import (
    MemberMatchdict,
    MemberIdMatchdict,
)
from c3smembership.presentation.views.dues_year import DUES_YEARS
from c3smembership.presentation.view_processing import \
    ColanderMatchdictValidator

LOG = logging.getLogger(__name__)


def get_member_details(request, member):
    """
    Gets the member details.
    """
    shares = request.registry.share_information.get_member_shares(
        member.membership_number)
    general_assembly_invitations = sorted(
        request.registry.general_assembly_invitation.get_member_invitations(
            member),
        key=lambda ga: ga['date'],
        reverse=True)

    dues = []
    latest_dues_year = str(max(DUES_YEARS))
    for year in sorted(DUES_YEARS, reverse=True):
        applicable = (
            member.membership_date < date(year, 12, 31)
            and (
                member.membership_loss_date is None
                or member.membership_loss_date >= date(year, 1, 1)))
        if not applicable:
            continue
        short = '{0:02d}'.format(year % 100)
        year_dues = member.get_dues(year, create=False)
        invoices = DuesInvoiceRepository.get_by_membership_number(
            member.membership_number, [year])
        dues.append({
            'year': str(year),
            'year_short': short,
            'invoices': invoices,
            'email_sent': year_dues.invoice,
            'email_sent_timestamp': year_dues.invoice_date,
            'has_invoice': len(invoices) > 0,
            'dues_start': year_dues.start,
            'dues_amount': year_dues.amount,
            'is_reduced': year_dues.reduced,
            'reduced_amount': year_dues.amount_reduced,
            'is_balanced': year_dues.balanced,
            'balance': year_dues.balance,
            'amount_paid': year_dues.amount_paid,
            'payment_received': year_dues.paid,
            'paid_date': year_dues.paid_date,
            'send_email_route': request.route_url(
                'send_dues{0}_invoice_email'.format(short),
                member_id=member.id),
            'reduction_route': request.route_url(
                'dues{0}_reduction'.format(short), member_id=member.id),
            'invoice_listing_route': request.route_url(
                'dues{0}_listing'.format(short)),
            'dues_notice_route': request.route_url(
                'dues{0}_notice'.format(short), member_id=member.id),
            'dues_invoice_pdf_backend':
                'dues{0}_invoice_pdf_backend'.format(short),
            'dues_reversal_pdf_backend':
                'dues{0}_reversal_pdf_backend'.format(short),
            'dues_notice_message_to_staff':
                'dues{0}notice_message_to_staff'.format(short),
        })

    return {
        'dues': dues,
        'date': date,
        'D': Decimal,
        'member': member,
        'shares': shares,
        'general_assembly_invitations': general_assembly_invitations,
        'latest_dues_year': latest_dues_year,
    }


@view_config(
    route_name='member_details',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberMatchdict(error_route='dashboard')
    ),
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_detail.pt',
)
def member_details(request):
    """
    This view lets accountants view member details:

    - has their signature arrived?
    - how about the payment?

    Mostly all the info about an application or membership
    in the database can be seen here.
    """
    member = request.validated_matchdict['member']

    logged_in = request.authenticated_userid
    LOG.info(
        'member details of membership number %s checked by %s',
        member.membership_number,
        logged_in)

    return get_member_details(request, member)


@view_config(
    route_name='detail',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_detail.pt',
)
def member_detail(request):
    """
    This view lets accountants view member details:

    - has their signature arrived?
    - how about the payment?

    Mostly all the info about an application or membership
    in the database can be seen here.
    """
    member = request.validated_matchdict['member']

    logged_in = request.authenticated_userid
    LOG.info('member details of id %s checked by %s', member.id, logged_in)

    return get_member_details(request, member)
