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
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository

LOG = logging.getLogger(__name__)


def get_member_details(request, member):
    """
    Gets the member details.
    """
    shares = request.registry.share_information.get_member_shares(
        member.membership_number)
    invoices15 = DuesInvoiceRepository.get_by_membership_number(
         member.membership_number, [2015])
    invoices16 = DuesInvoiceRepository.get_by_membership_number(
         member.membership_number, [2016])
    invoices17 = DuesInvoiceRepository.get_by_membership_number(
         member.membership_number, [2017])
    invoices18 = DuesInvoiceRepository.get_by_membership_number(
         member.membership_number, [2018])
    invoices19 = DuesInvoiceRepository.get_by_membership_number(
        member.membership_number, [2019])
    general_assembly_invitations = sorted(
        request.registry.general_assembly_invitation.get_member_invitations(
            member),
        key=lambda ga: ga['date'],
        reverse=True)

    dues = []
    if (member.membership_date < date(2015, 12, 31) and
            (
                member.membership_loss_date is None or
                member.membership_loss_date >= date(2015, 1, 1))):
        dues.append({
            'year': '2015',
            'year_short': '15',
            'invoices': invoices15,
            'email_sent': member.dues15_invoice,
            'email_sent_timestamp': member.dues15_invoice_date,
            'has_invoice': len(invoices15) > 0,
            'dues_start': member.dues15_start,
            'dues_amount': member.dues15_amount,
            'is_reduced': member.dues15_reduced,
            'reduced_amount': member.dues15_amount_reduced,
            'is_balanced': member.dues15_balanced,
            'amount_paid': member.dues15_amount_paid,
            'payment_received': member.dues15_paid,
            'paid_date': member.dues15_paid_date,
            'send_email_route': request.route_url(
                'send_dues15_invoice_email', member_id=member.id),
            'reduction_route': request.route_url(
                'dues15_reduction', member_id=member.id),
            'invoice_listing_route': request.route_url('dues15_listing'),
            'dues_notice_route': request.route_url(
                'dues15_notice', member_id=member.id),
            'dues_invoice_pdf_backend': 'dues15_invoice_pdf_backend',
            'dues_reversal_pdf_backend': 'dues15_reversal_pdf_backend',
            'dues_notice_message_to_staff': 'dues15notice_message_to_staff',
        })
    if (member.membership_date < date(2016, 12, 31) and
            (
                member.membership_loss_date is None or
                member.membership_loss_date >= date(2016, 1, 1))):
        dues.append({
            'year': '2016',
            'year_short': '16',
            'invoices': invoices16,
            'email_sent': member.dues16_invoice,
            'email_sent_timestamp': member.dues16_invoice_date,
            'has_invoice': len(invoices16) > 0,
            'dues_start': member.dues16_start,
            'dues_amount': member.dues16_amount,
            'is_reduced': member.dues16_reduced,
            'reduced_amount': member.dues16_amount_reduced,
            'is_balanced': member.dues16_balanced,
            'amount_paid': member.dues16_amount_paid,
            'payment_received': member.dues16_paid,
            'paid_date': member.dues16_paid_date,
            'send_email_route': request.route_url(
                'send_dues16_invoice_email', member_id=member.id),
            'reduction_route': request.route_url(
                'dues16_reduction', member_id=member.id),
            'invoice_listing_route': request.route_url('dues16_listing'),
            'dues_notice_route': request.route_url(
                'dues16_notice', member_id=member.id),
            'dues_invoice_pdf_backend': 'dues16_invoice_pdf_backend',
            'dues_reversal_pdf_backend': 'dues16_reversal_pdf_backend',
            'dues_notice_message_to_staff': 'dues16notice_message_to_staff',
        })
    if (member.membership_date < date(2017, 12, 31) and
            (
                member.membership_loss_date is None or
                member.membership_loss_date >= date(2017, 1, 1))):
        dues.append({
            'year': '2017',
            'year_short': '17',
            'invoices': invoices17,
            'email_sent': member.dues17_invoice,
            'email_sent_timestamp': member.dues17_invoice_date,
            'has_invoice': len(invoices17) > 0,
            'dues_start': member.dues17_start,
            'dues_amount': member.dues17_amount,
            'is_reduced': member.dues17_reduced,
            'reduced_amount': member.dues17_amount_reduced,
            'is_balanced': member.dues17_balanced,
            'amount_paid': member.dues17_amount_paid,
            'payment_received': member.dues17_paid,
            'paid_date': member.dues17_paid_date,
            'send_email_route': request.route_url(
                'send_dues17_invoice_email', member_id=member.id),
            'reduction_route': request.route_url(
                'dues17_reduction', member_id=member.id),
            'invoice_listing_route': request.route_url('dues17_listing'),
            'dues_notice_route': request.route_url(
                'dues17_notice', member_id=member.id),
            'dues_invoice_pdf_backend': 'dues17_invoice_pdf_backend',
            'dues_reversal_pdf_backend': 'dues17_reversal_pdf_backend',
            'dues_notice_message_to_staff': 'dues17notice_message_to_staff',
        })
    if (member.membership_date < date(2018, 12, 31) and
            (
                member.membership_loss_date is None or
                member.membership_loss_date >= date(2018, 1, 1))):
        dues.append({
            'year': '2018',
            'year_short': '18',
            'invoices': invoices18,
            'email_sent': member.dues18_invoice,
            'email_sent_timestamp': member.dues18_invoice_date,
            'has_invoice': len(invoices18) > 0,
            'dues_start': member.dues18_start,
            'dues_amount': member.dues18_amount,
            'is_reduced': member.dues18_reduced,
            'reduced_amount': member.dues18_amount_reduced,
            'is_balanced': member.dues18_balanced,
            'amount_paid': member.dues18_amount_paid,
            'payment_received': member.dues18_paid,
            'paid_date': member.dues18_paid_date,
            'send_email_route': request.route_url(
                'send_dues18_invoice_email', member_id=member.id),
            'reduction_route': request.route_url(
                'dues18_reduction', member_id=member.id),
            'invoice_listing_route': request.route_url('dues18_listing'),
            'dues_notice_route': request.route_url(
                'dues18_notice', member_id=member.id),
            'dues_invoice_pdf_backend': 'dues18_invoice_pdf_backend',
            'dues_reversal_pdf_backend': 'dues18_reversal_pdf_backend',
            'dues_notice_message_to_staff': 'dues18notice_message_to_staff',
        })
    if (member.membership_date < date(2019, 12, 31) and
            (
                member.membership_loss_date is None or
                member.membership_loss_date >= date(2019, 1, 1))):
        dues.append({
            'year': '2019',
            'year_short': '19',
            'invoices': invoices19,
            'email_sent': member.dues19_invoice,
            'email_sent_timestamp': member.dues19_invoice_date,
            'has_invoice': len(invoices19) > 0,
            'dues_start': member.dues19_start,
            'dues_amount': member.dues19_amount,
            'is_reduced': member.dues19_reduced,
            'reduced_amount': member.dues19_amount_reduced,
            'is_balanced': member.dues19_balanced,
            'amount_paid': member.dues19_amount_paid,
            'payment_received': member.dues19_paid,
            'paid_date': member.dues19_paid_date,
            'send_email_route': request.route_url(
                'send_dues19_invoice_email', member_id=member.id),
            'reduction_route': request.route_url(
                'dues19_reduction', member_id=member.id),
            'invoice_listing_route': request.route_url('dues19_listing'),
            'dues_notice_route': request.route_url(
                'dues19_notice', member_id=member.id),
            'dues_invoice_pdf_backend': 'dues19_invoice_pdf_backend',
            'dues_reversal_pdf_backend': 'dues19_reversal_pdf_backend',
            'dues_notice_message_to_staff': 'dues19notice_message_to_staff',
        })

    return {
        'dues': dues,
        'date': date,
        'D': Decimal,
        'member': member,
        'shares': shares,
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
