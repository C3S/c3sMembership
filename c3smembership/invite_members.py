# -*- coding: utf-8 -*-

"""
This module has functionality to invite members to C3S events like the General
Assembly and BarCamp.

- Email templates (en/de)
- Check and send email (view)
- Batch invite n members (view)

The first use was for the C3S HQ inauguration party in February 2014.

It was then reused for:

- BarCamp and General Assembly 2014
- BarCamp and General Assembly 2015
- BarCamp and General Assembly 2016
- BarCamp and General Assembly 2017
- BarCamp and General Assembly 2018

How it works
------------

We send an email to the members from our membership database -- this app. The
templates for those emails (english/german depending on members locale) can be
prepared here.

For convenience, staff can invite n members at the same time.

Combination with c3sPartyTicketing
----------------------------------

Invitation emails are usually prepped with links to the C3S ticketing system
(*c3sPartyTicketing*). That other webapp can be configured to fetch information
about the relevant C3S member from this app via API call, see the relevant
module.
"""

from datetime import datetime
import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_mailer.message import Message

from c3smembership.invite_members_texts import make_bcga18_invitation_email
from c3smembership.mail_utils import send_message
from c3smembership.membership_certificate import make_random_token
from c3smembership.models import C3sMember
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)


DEBUG = False
LOG = logging.getLogger(__name__)
URL_PATTERN = '{ticketing_url}/lu/{token}/{email}'


@view_config(permission='manage',
             route_name='invite_member')
def invite_member_bcgv(request):
    """
    Send email to member with link to ticketing.

    === ====================================
    URL http://app:port/invite_member/{m_id}
    === ====================================
    """
    member_id = request.matchdict['m_id']
    member = C3sMember.get_by_id(member_id)
    if member is None:
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return get_memberhip_listing_redirect(request)

    if not member.is_member():
        request.session.flash(
            'Invitations can only be sent to members.',
            'messages')
        return get_memberhip_listing_redirect(request, member_id)

    # prepare a random token iff none is set
    if member.email_invite_token_bcgv18 is None:
        member.email_invite_token_bcgv18 = make_random_token()
    url = URL_PATTERN.format(
        ticketing_url=request.registry.settings['ticketing.url'],
        token=member.email_invite_token_bcgv18,
        email=member.email)

    LOG.info("mailing event invitation to to member id %s", member.id)

    email_subject, email_body = make_bcga18_invitation_email(member, url)
    message = Message(
        subject=email_subject,
        sender='yes@c3s.cc',
        recipients=[member.email],
        body=email_body,
        extra_headers={
            'Reply-To': 'office@c3s.cc',
            }
    )
    send_message(request, message)

    # member._token = _looong_token
    member.email_invite_flag_bcgv18 = True
    member.email_invite_date_bcgv18 = datetime.now()
    return get_memberhip_listing_redirect(request, member.id)


@view_config(
    route_name="invite_batch",
    permission='manage')
def batch_invite(request):
    """
    Batch invite n members at the same time.

    The number (n) is configurable, defaults to 5.
    The number can either be supplied in the URL
    or by posting a form with 'number' and 'submit to this view.

    === =====================================
    URL http://app:port/invite_batch/{number}
    === =====================================
    """
    try:  # how many to process?
        batch_count = int(request.matchdict['number'])
    except (ValueError, KeyError):
        batch_count = 5
    if 'submit' in request.POST:
        try:
            batch_count = int(request.POST['number'])
        except ValueError:
            batch_count = 5

    invitees = C3sMember.get_invitees(batch_count)

    if len(invitees) == 0:
        request.session.flash('no invitees left. all done!',
                              'message_to_staff')
        return HTTPFound(request.route_url('toolbox'))

    num_sent = 0
    ids_sent = []

    for member in invitees:
        # prepare a random token iff none is set
        if member.email_invite_token_bcgv18 is None:
            member.email_invite_token_bcgv18 = make_random_token()
        url = URL_PATTERN.format(
            ticketing_url=request.registry.settings['ticketing.url'],
            token=member.email_invite_token_bcgv18,
            email=member.email)

        LOG.info("mailing event invitation to to member id %s", member.id)

        email_subject, email_body = make_bcga18_invitation_email(member, url)
        message = Message(
            subject=email_subject,
            sender='yes@c3s.cc',
            recipients=[member.email],
            body=email_body,
            extra_headers={
                'Reply-To': 'office@c3s.cc',
            }
        )
        send_message(request, message)

        member.email_invite_flag_bcgv18 = True
        member.email_invite_date_bcgv18 = datetime.now()
        num_sent += 1
        ids_sent.append(member.id)

    request.session.flash(
        "sent out {} mails (to members with ids {})".format(
            num_sent, ids_sent),
        'message_to_staff')

    return HTTPFound(request.route_url('toolbox'))
