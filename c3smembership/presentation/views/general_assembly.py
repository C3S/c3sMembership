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

import deform
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid_mailer.message import Message

from c3smembership.mail_utils import (
    get_template_text,
    get_email_footer,
    get_salutation,
    send_message,
)
from c3smembership.presentation.schemas.general_assembly import (
    GeneralAssemblyMatchdict,
    GeneralAssemblyInvitationMatchdict,
    BatchInvitePost,
    GeneralAssemblyFormFactory,
)
from c3smembership.presentation.view_processing import (
    ColanderMatchdictValidator,
    ColanderPostValidator,
    FlashCallbackErrorHandler,
    MultiPreProcessor,
)
from c3smembership.presentation.views.membership_certificate import (
    make_random_token,
)
from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)


DEBUG = False
LOG = logging.getLogger(__name__)
URL_PATTERN = '{ticketing_url}/lu/{token}/{email}'
CURRENT_GENERAL_ASSEMBLY = 7
BODY_TEMPLATE = 'bcga2019_invite_body'
SUBJECT_TEMPLATE = 'bcga2019_invite_subject'


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
        request.registry.general_assembly_invitation.get_general_assemblies(),
        key=lambda ga: ga.number,
        reverse=True)
    return {'general_assemblies': assemblies}


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'general_assembly.pt',
    permission='manage',
    route_name='general_assembly',
    pre_processor=ColanderMatchdictValidator(
        GeneralAssemblyMatchdict(error_route='general_assemblies'),
    ),
)
def general_assembly_view(request):
    """
    Show general assembly
    """
    assembly = request.validated_matchdict['general_assembly']
    return {
        'number': assembly.number,
        'name': assembly.name,
        'date': assembly.date,
    }


@view_config(
    permission='manage',
    route_name='general_assembly_invitation',
    pre_processor=ColanderMatchdictValidator(
        GeneralAssemblyInvitationMatchdict(error_route='general_assemblies'),
    ),
)
def general_assembly_invitation(request):
    """
    Invite member to general assembly
    """
    general_assembly = request.validated_matchdict['general_assembly']
    member = request.validated_matchdict['member']
    send_invitation(request, member, general_assembly.number)
    # As in other places the route url pattern is hard-coded but should not be.
    # The only place to change the route url pattern must be the configuration
    # and therefore this hard-coding is error-prone. It should be referenced
    # like route_url() but then route_url may require the passing of a
    # parameter which is not known. Another way must be found to do this
    # dynamically.
    if '/members/' in request.referer:
        return HTTPFound(
            request.route_url(
                'member_details',
                membership_number=member.membership_number,
                _anchor='general-assembly'))
    else:
        return HTTPFound(request.route_url(
            'membership_listing_backend',
            _anchor='member_{id}'.format(id=member.id)))


def make_bcga_invitation_email(member, url):
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
            get_template_text(SUBJECT_TEMPLATE, member.locale)))
        print(u"the salutation: {}".format(get_salutation(member)))
        print(u"the footer: {}".format(get_email_footer(member.locale)))
        print(u"the body: {}".format(
            get_template_text(BODY_TEMPLATE, member.locale).format(
                salutation=get_salutation(member),
                invitation_url=url,
                footer=get_email_footer(member.locale))))
    return (
        get_template_text(SUBJECT_TEMPLATE, member.locale).rstrip(
            '\n'),  # remove newline (\n) from mail subject
        get_template_text(BODY_TEMPLATE, member.locale).format(
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
        assembly = GeneralAssemblyRepository.get_general_assembly(
            general_assembly_number)
        request.registry.general_assembly_invitation.invite_member(
            member,
            assembly,
            token)
        url = URL_PATTERN.format(
            ticketing_url=request.registry.settings['ticketing.url'],
            token=token,
            email=member.email)
        LOG.info("mailing event invitation to to member id %s", member.id)

        email_subject, email_body = make_bcga_invitation_email(member, url)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[member.email],
            body=email_body,
        )
        send_message(request, message)


def post_error_handler(request, schema, errors):
    """
    Redirect to specific general assembly on POST data validation error

    The matchdict containing the general assembly number is validated before
    and the POST data is only validated if the matchdict validation was
    successful. Therefore, a redirect to the specific general assembly is
    possible.
    """
    # pylint: disable=unused-argument
    general_assembly = request.validated_matchdict['general_assembly']
    return HTTPFound(
        request.route_url(
            'general_assembly',
            number=general_assembly.number))


@view_config(
    route_name='general_assembly_batch_invite',
    permission='manage',
    pre_processor=MultiPreProcessor([
        ColanderMatchdictValidator(
            GeneralAssemblyMatchdict(error_route='general_assemblies'),
        ),
        ColanderPostValidator(
            BatchInvitePost(),
            FlashCallbackErrorHandler(post_error_handler),
        ),
    ]),
)
def batch_invite(request):
    """
    Batch invite n members at the same time.
    """
    general_assembly = request.validated_matchdict['general_assembly']
    count = request.validated_post['count']

    invitees = GeneralAssemblyRepository.get_invitees(
        general_assembly.number, count)

    if len(invitees) == 0:
        request.session.flash('no invitees left. all done!',
                              'success')
        return HTTPFound(request.route_url(
            'general_assembly', number=general_assembly.number))

    num_sent = 0
    membership_numbers_sent = []

    for member in invitees:
        try:
            send_invitation(request, member, general_assembly.number)
        except ValueError as value_error:
            request.session.flash(
                unicode(value_error.message),
                'danger')
            return HTTPFound(request.route_url(
                'general_assembly', number=general_assembly.number))

        num_sent += 1
        membership_numbers_sent.append(member.membership_number)

    request.session.flash(
        "sent out {} mails (to members with membership numbers {})".format(
            num_sent, membership_numbers_sent),
        'success')

    return HTTPFound(request.route_url(
        'general_assembly', number=general_assembly.number))


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'general_assembly_create.pt',
    route_name='general_assembly_create',
    permission='manage')
def general_assembly_create(request):
    """
    Create a general assembly
    """
    form = GeneralAssemblyFormFactory.create()
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            request.registry.general_assembly_invitation \
                .create_general_assembly(
                    appstruct['general_assembly']['name'],
                    appstruct['general_assembly']['date'])
            return HTTPFound(request.route_url('general_assemblies'))
        except deform.ValidationFailure as validationfailure:
            return {'form': validationfailure.render()}
    elif 'cancel' in request.POST:
        return HTTPFound(request.route_url('general_assemblies'))
    else:
        number = request.registry.general_assembly_invitation \
            .get_next_number()
        form.set_appstruct({'general_assembly': {'number': number}})
        return {'form': form.render()}


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'general_assembly_edit.pt',
    route_name='general_assembly_edit',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        GeneralAssemblyMatchdict(error_route='general_assemblies'),
    ),
)
def general_assembly_edit(request):
    """
    Edit a general assembly
    """
    assembly = request.validated_matchdict['general_assembly']
    form = GeneralAssemblyFormFactory.create()
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            request.registry.general_assembly_invitation \
                .edit_general_assembly(
                    assembly.number,
                    appstruct['general_assembly']['name'],
                    appstruct['general_assembly']['date'])
            return HTTPFound(request.route_url(
                'general_assembly', number=assembly.number))
        except deform.ValidationFailure as validationfailure:
            return {'form': validationfailure.render()}
    elif 'cancel' in request.POST:
        return HTTPFound(request.route_url(
            'general_assembly', number=assembly.number))
    else:
        form.set_appstruct({'general_assembly': {
            'number': assembly.number,
            'name': assembly.name,
            'date': assembly.date}})
        return {'form': form.render()}
