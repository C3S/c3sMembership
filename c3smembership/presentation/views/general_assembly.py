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
from c3smembership.data.repository.general_assembly import \
    GeneralAssemblyRepository


DEBUG = False
LOG = logging.getLogger(__name__)
URL_PATTERN = '{ticketing_url}/lu/{token}/{email}'
INVITATION_TEXT_PREVIEW_LENGTH = 250
TRUNCATE_CHARACTERS = [' ', '\r', '\n']


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


def truncate_value(value, length, truncate_characters):
    """
    Truncate a string after length on defined characters

    The string is truncated at the first appearance of a defined truncate
    character in order to not truncate in between words or HTML tags.

    Truncate characters are

    Args:
        value: String. The value to be truncated.
        length: Integeger. The length after which the value is truncated.
        truncate_characters: Array of characters. The characters at which the
            value is truncated.

    Returns:
        The value truncated at the first appearance of a truncate character
        after the specified length.
    """
    pos = length
    while value[pos] not in truncate_characters:
        pos += 1
    return value[:pos]


def get_invitation_display_texts(invitation_text, length):
    """
    Get the invitation text and preview text to display

    The display text has line breaks replaced by a HTML BR tag.

    Args:
        invitation_text: String. The text for which the display text and its
            preview is returned.
        length: Integer. The number of characters after which the text is
            truncated at a suitable character to create the preview.

    Returns:
        Set of invitation text and invitation text preview
    """
    if not invitation_text:
        return (u'', u'')
    invitation_text = invitation_text.replace('\n', '\x3Cbr />')
    invitation_text_preview = invitation_text
    if len(invitation_text_preview) > length:
        invitation_text_preview = truncate_value(
            invitation_text_preview,
            length,
            TRUNCATE_CHARACTERS)
    return invitation_text, invitation_text_preview


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

    invitation_text_en, invitation_text_en_preview = \
        get_invitation_display_texts(
            assembly.invitation_text_en,
            INVITATION_TEXT_PREVIEW_LENGTH)
    invitation_text_de, invitation_text_de_preview = \
        get_invitation_display_texts(
            assembly.invitation_text_de,
            INVITATION_TEXT_PREVIEW_LENGTH)

    return {
        'number': assembly.number,
        'name': assembly.name,
        'date': assembly.date,
        'invitation_subject_en': assembly.invitation_subject_en,
        'invitation_text_en': invitation_text_en,
        'invitation_text_en_preview': invitation_text_en_preview,
        'invitation_subject_de': assembly.invitation_subject_de,
        'invitation_text_de': invitation_text_de,
        'invitation_text_de_preview': invitation_text_de_preview,
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
    return HTTPFound(request.route_url(
        'membership_listing_backend',
        _anchor='member_{id}'.format(id=member.id)))


def send_invitation(request, member, general_assembly_number):
    """
    Sends an invitation email to the member and records the invitation.

    Args:
        request: The Pyramid request used to access configuration, get the
            mailer and return notifications.
        member: The member to which the invitation is sent.
    """
    if not member.is_member():
        raise ValueError('Invitations can only be sent to members.')

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

        email_subject = assembly.invitation_subject_de if \
            member.locale == 'de' else assembly.invitation_subject_en
        invitation_text = assembly.invitation_text_de if \
            member.locale == 'de' else assembly.invitation_text_en
        email_body = invitation_text.format(
            salutation=get_salutation(member),
            invitation_url=url,
            footer=get_email_footer(member.locale)
        )

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
                    appstruct['general_assembly']['date'],
                    appstruct['general_assembly']['invitation_subject_en'],
                    appstruct['general_assembly']['invitation_text_en'],
                    appstruct['general_assembly']['invitation_subject_de'],
                    appstruct['general_assembly']['invitation_text_de'])
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
                    appstruct['general_assembly']['date'],
                    appstruct['general_assembly']['invitation_subject_en'],
                    appstruct['general_assembly']['invitation_text_en'],
                    appstruct['general_assembly']['invitation_subject_de'],
                    appstruct['general_assembly']['invitation_text_de'])
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
            'date': assembly.date,
            'invitation_subject_en': assembly.invitation_subject_en,
            'invitation_text_en': assembly.invitation_text_en,
            'invitation_subject_de': assembly.invitation_subject_de,
            'invitation_text_de': assembly.invitation_text_de}})
        return {'form': form.render()}
