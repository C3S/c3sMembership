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
# pylint: disable=superfluous-parens

import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_mailer.message import Message

from c3smembership.mail_utils import (
    get_template_text,
    get_email_footer,
    get_salutation,
    send_message,
)
from c3smembership.presentation.views.membership_certificate import (
    make_random_token,
)
from c3smembership.data.repository.member_repository import MemberRepository
from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)


DEBUG = False
LOG = logging.getLogger(__name__)
URL_PATTERN = '{ticketing_url}/lu/{token}/{email}'
CURRENT_GENERAL_ASSEMBLY = 5


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'general_assemblies.pt',
    permission='manage',
    route_name='general_assemblies')
def general_assemblies(request):
    """
    List general assemblies
    """
    # pylint: disable=unused-argument
    assemblies = sorted(
        GeneralAssemblyRepository.get_general_assemblies(),
        key=lambda ga: ga.number,
        reverse=True)
    return {'general_assemblies': assemblies}


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'general_assembly.pt',
    permission='manage',
    route_name='general_assembly')
def general_assembly(request):
    """
    Show general assembly
    """
    result = {
        'number': None,
        'name': None,
        'date': None,
    }
    number_str = request.matchdict.get('number')
    number = None
    try:
        number = int(number_str)
    except ValueError:
        number = None
    assembly = GeneralAssemblyRepository.get_general_assembly(number)
    if assembly is not None:
        result['number'] = assembly.number
        result['name'] = assembly.name
        result['date'] = assembly.date
    return result


@view_config(
    permission='manage',
    route_name='general_assembly_invitation')
def general_assembly_invitation(request):
    """
    Invite member to general assembly
    """
    general_assembly_number = None
    try:
        general_assembly_number = int(request.matchdict.get('number'))
    except (ValueError, TypeError):
        request.session.flash(
            'Invalid general assembly number',
            'message_to_staff')
        return HTTPFound(request.route_url('general_assemblies'))

    membership_number = None
    try:
        membership_number = int(request.matchdict.get('membership_number'))
    except (ValueError, TypeError):
        request.session.flash(
            'Invalid membership number',
            'message_to_staff')
        return HTTPFound(request.route_url(
            'general_assembly', number=general_assembly_number))
    member = request.registry.member_information.get_member(membership_number)
    if member is None:
        request.session.flash(
            'Invalid membership number',
            'message_to_staff')
        return HTTPFound(request.route_url(
            'general_assembly', number=general_assembly_number))

    send_invitation(request, member, general_assembly_number)
    return HTTPFound(
        request.route_url('general_assembly', number=general_assembly_number))


def make_bcga18_invitation_email(member, url):
    """
    Create email subject and body for an invitation email for members.

    Returns:
        Tuple: message subject and body in users language.
    """
    if DEBUG:  # pragma: no cover
        print(u"the member: {}".format(member))
        print(u"the member.locale: {}".format(member.locale))
        print(u"the url: {}".format(url))
        print(u"the subject: {}".format(
            get_template_text('bcga2018_invite_subject', member.locale)))
        print(u"the salutation: {}".format(get_salutation(member)))
        print(u"the footer: {}".format(get_email_footer(member.locale)))
        print(u"the body: {}".format(
            get_template_text('bcga2018_invite_body', member.locale).format(
                salutation=get_salutation(member),
                invitation_url=url,
                footer=get_email_footer(member.locale))))
    return (
        get_template_text('bcga2018_invite_subject', member.locale).rstrip(
            '\n'),  # remove newline (\n) from mail subject
        get_template_text('bcga2018_invite_body', member.locale).format(
            salutation=get_salutation(member),
            invitation_url=url,
            footer=get_email_footer(member.locale)
        )
    )


def send_invitation(request, member, general_assembly_number):
    """
    Sends an invitation email to the member and records the invitation.

    Args:
        request: The Pyramid request used to access configuration, get the
            mailer and return notifications.
        member: The member to which the invitation is sent.
    """
    if not member.is_member():
        request.session.flash(
            'Invitations can only be sent to members.',
            'danger')
        return get_memberhip_listing_redirect(request, member.id)

    invitation = GeneralAssemblyRepository.get_member_invitation(
        member.membership_number,
        general_assembly_number)
    if invitation is None or not invitation['flag']:
        token = make_random_token()
        url = URL_PATTERN.format(
            ticketing_url=request.registry.settings['ticketing.url'],
            token=token,
            email=member.email)
        LOG.info("mailing event invitation to to member id %s", member.id)

        email_subject, email_body = make_bcga18_invitation_email(member, url)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[member.email],
            body=email_body,
        )
        send_message(request, message)

        assembly = GeneralAssemblyRepository.get_general_assembly(
            general_assembly_number)
        request.registry.general_assembly_invitation.invite_member(
            member,
            assembly,
            token)


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

    invitees = GeneralAssemblyRepository.get_invitees(batch_count)

    if len(invitees) == 0:
        request.session.flash('no invitees left. all done!',
                              'success')
        return HTTPFound(request.route_url('toolbox'))

    num_sent = 0
    ids_sent = []

    for member in invitees:
        send_invitation(request, member, CURRENT_GENERAL_ASSEMBLY)
        num_sent += 1
        ids_sent.append(member.id)

    request.session.flash(
        "sent out {} mails (to members with ids {})".format(
            num_sent, ids_sent),
        'success')

    return HTTPFound(request.route_url('toolbox'))
