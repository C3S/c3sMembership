# -*- coding: utf-8 -*-
"""
Membership acquisition

- Mail signature reminder email
- Confirm signature reception
- Mail signature reception confirmation email
- Mail payment reminder email
- Confirm payment reception
- Mail payment reception confirmation email
- Send email address verification email
- Delete a range of membership applications
"""

from datetime import datetime
import logging

import colander
import deform
from deform import ValidationFailure
from pyramid_mailer.message import Message
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from pyramid.view import view_config

from c3smembership.mail_utils import (
    format_date,
    get_email_footer,
    get_salutation,
    get_template_text,
    make_payment_confirmation_email,
    send_message,
)
from c3smembership.data.model.base.c3smember import (
    C3sMember,
    InvalidPropertyException,
    InvalidSortDirection,
)
from c3smembership.presentation.parameter_validation import (
    ParameterValidationException,
)
from c3smembership.presentation.schemas.member import MemberIdMatchdict
from c3smembership.presentation.view_processing import \
    ColanderMatchdictValidator
from c3smembership.presentation.views.join import send_mail_confirmation_mail
from c3smembership.utils import generate_pdf


LOG = logging.getLogger(__name__)


@view_config(
    renderer='c3smembership.presentation:'
             'templates/pages/membership_acquisition.pt',
    permission='manage',
    route_name='dashboard')
def dashboard(request):
    """
    The Dashboard.

    This view lets accountants view
    the **list of applications for membership**.

    Some details can be seen (name, email, link to more details)
    as well as their membership application *progress*:

    - has their signature arrived?
    - how about the payment?
    - have reminders been sent? receptions confirmed?

    There are also links to *edit* or *delete* one of the datasets.

    Once all requirements are fulfilled,
    an application can be turned into a membership from here:
    a button shows up.
    """

    pagination = request.pagination
    try:
        members = C3sMember.nonmember_listing(
            pagination.paging.content_offset,
            pagination.paging.page_size,
            pagination.sorting.sort_property,
            pagination.sorting.sort_direction)
    except (InvalidPropertyException, InvalidSortDirection):
        raise ParameterValidationException(
            'Page does not exist.',
            request.route_url(request.matched_route.name))
    return {
        'members': members,
    }


def dashboard_content_size_provider(request):
    """
    Provide non-member listing count as a content size provider to pagination
    """
    # pylint: disable=unused-argument
    # TODO: Architectural cleanup necessary as the presentation layer
    # is directly accessing the data layer. It should instead access the
    # business layer.
    return C3sMember.nonmember_listing_count()


def get_dashboard_redirect(request, member_id=''):
    """Get the redirect for the dashboard.

    Gets an HTTPFound for redirection to the dashboard including passing page
    number and sorting information from cookies as well as setting an anchor
    on the member identified by member_id.

    Args:
        request: The request which is being processed.
        member_id: Optional value of a member on which to set an anchor in the
            redirection.

    Returns:
        A HTTPFound for redirection to the dashboard.
    """
    kwargs = {}
    if type(member_id) == str or type(member_id) == unicode:
        member_id_str = member_id
    else:
        member_id_str = str(member_id)
    if len(member_id_str) > 0:
        kwargs['_anchor'] = 'member_{id}'.format(id=member_id_str)

    return HTTPFound(request.route_url('dashboard', **kwargs))


def make_signature_reminder_email(member):
    '''
    a mail body to remind membership applicants
    to send the form with their signature
    '''
    return (
        get_template_text('signature_reminder_subject', member.locale),
        get_template_text('signature_reminder_body', member.locale).format(
            salutation=get_salutation(member),
            submission_date=format_date(
                member.date_of_submission,
                member.locale),
            footer=get_email_footer(member.locale)))


def make_payment_reminder_email(member):
    '''
    a mail body to remind membership applicants
    to send the payment for their shares
    '''
    return (
        get_template_text('payment_reminder_subject', member.locale),
        get_template_text('payment_reminder_body', member.locale).format(
            salutation=get_salutation(member),
            submission_date=format_date(
                member.date_of_submission,
                member.locale),
            shares_value=int(member.num_shares) * 50,
            shares_count=member.num_shares,
            transfer_purpose=u'C3Shares ' + member.email_confirm_code,
            footer=get_email_footer(member.locale)))


@view_config(
    route_name='switch_sig',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def switch_sig(request):
    """
    This view lets accountants switch an applications signature status
    once their signature has arrived.

    Note:
        Expects the object request.registry.membership_application to implement
    """
    member = request.validated_matchdict['member']

    membership_application = request.registry.membership_application
    signature_received = membership_application.get_signature_status(member.id)
    new_signature_received = not signature_received
    membership_application.set_signature_status(
        member.id,
        new_signature_received)

    LOG.info(
        "signature status of member.id %s changed by %s to %s",
        member.id,
        request.user.login,
        new_signature_received
    )

    if request.referer is not None and 'dashboard' in request.referer:
        return get_dashboard_redirect(request, member.id)
    else:
        return HTTPFound(
            request.route_url(
                'detail',
                member_id=member.id,
                _anchor='membership_info'
            )
        )


@view_config(
    route_name='switch_pay',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def switch_pay(request):
    """
    This view lets accountants switch a member applications payment status once
    their payment has arrived.
    """
    member = request.validated_matchdict['member']

    membership_application = request.registry.membership_application
    payment_received = membership_application.get_payment_status(member.id)
    new_payment_received = not payment_received
    membership_application.set_payment_status(
        member.id,
        new_payment_received)

    LOG.info(
        "payment info of member.id %s changed by %s to %s",
        member.id,
        request.user.login,
        new_payment_received
    )
    if request.referer is not None and 'dashboard' in request.referer:
        return get_dashboard_redirect(request, member.id)
    else:
        return HTTPFound(
            request.route_url(
                'detail',
                member_id=member.id,
                _anchor='membership_info')
        )


@view_config(
    route_name='regenerate_pdf',
    permission='manage',
)
def regenerate_pdf(request):
    """
    Staffers can regenerate an applicants PDF and send it to her.
    """
    code = request.matchdict['code']
    member = C3sMember.get_by_code(code)

    if member is None:
        request.session.flash(
            'A member with code {} does not exist'.format(code),
            'danger')
        return get_dashboard_redirect(request)

    membership_application = request.registry.membership_application.get(
        member.id)

    appstruct = {
        'firstname': member.firstname,
        'lastname': member.lastname,
        'address1': member.address1,
        'address2': member.address2,
        'postcode': member.postcode,
        'city': member.city,
        'email': member.email,
        'email_confirm_code': membership_application['payment_token'],
        'country': member.country,
        'locale': member.locale,
        'membership_type': membership_application['membership_type'],
        'num_shares': membership_application['shares_quantity'],
        'date_of_birth': member.date_of_birth,
        'date_of_submission': membership_application['date_of_submission'],
    }
    LOG.info(
        "%s regenerated the PDF for code %s",
        authenticated_userid(request),
        code)
    return generate_pdf(request, appstruct)


@view_config(
    route_name='mail_sig_confirmation',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def mail_signature_confirmation(request):
    """
    Send a mail to a membership applicant informing her about reception of
    signature.
    """
    member = request.validated_matchdict['member']

    membership_application = request.registry.membership_application
    membership_application.mail_signature_confirmation(member.id, request)

    if request.referer is not None and 'detail' in request.referer:
        return HTTPFound(request.route_url(
            'detail',
            member_id=member.id))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(
    route_name='mail_pay_confirmation',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def mail_payment_confirmation(request):
    """
    Send a mail to a membership applicant
    informing her about reception of payment.
    """
    member = request.validated_matchdict['member']

    email_subject, email_body = make_payment_confirmation_email(member)
    message = Message(
        subject=email_subject,
        sender=request.registry.settings['c3smembership.notification_sender'],
        recipients=[member.email],
        body=email_body,
    )
    send_message(request, message)

    member.payment_confirmed = True
    member.payment_confirmed_date = datetime.now()
    if request.referer is not None and 'detail' in request.referer:
        return HTTPFound(request.route_url(
            'detail',
            member_id=member.id))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(
    route_name='mail_sig_reminder',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def mail_signature_reminder(request):
    """
    Send a mail to a membership applicant
    reminding her about lack of *signature*.
    Headquarters is still waiting for the *signed form*.

    This view can only be used by staff.

    To be approved for membership applicants have to

    * Transfer money for the shares to acquire (at least one share).
    * **Send the signed form** back to headquarters.
    """
    member = request.validated_matchdict['member']

    email_subject, email_body = make_signature_reminder_email(member)
    message = Message(
        subject=email_subject,
        sender=request.registry.settings['c3smembership.notification_sender'],
        recipients=[member.email],
        body=email_body
    )
    send_message(request, message)

    if member.sent_signature_reminder is None or \
            member.sent_signature_reminder == 0:
        member.sent_signature_reminder = 1
    else:
        member.sent_signature_reminder += 1
    member.sent_signature_reminder_date = datetime.now()

    if request.referer is not None and 'detail' in request.referer:
        return HTTPFound(request.route_url(
            'detail',
            member_id=member.id))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(
    route_name='mail_pay_reminder',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def mail_payment_reminder(request):
    """
    Send a mail to a membership applicant
    reminding her about lack of **payment**.
    Headquarters is still waiting for the **bank transfer**.

    This view can only be used by staff.

    To be approved for membership applicants have to

    * **Transfer money** for the shares to acquire (at least one share).
    * Send the signed form back to headquarters.
    """
    member = request.validated_matchdict['member']

    email_subject, email_body = make_payment_reminder_email(member)
    message = Message(
        subject=email_subject,
        sender=request.registry.settings['c3smembership.notification_sender'],
        recipients=[member.email],
        body=email_body
    )
    send_message(request, message)

    if member.sent_payment_reminder is None or \
            member.sent_payment_reminder == 0:
        member.sent_payment_reminder = 1
    else:
        member.sent_payment_reminder += 1
    member.sent_payment_reminder_date = datetime.now()

    if request.referer is not None and 'detail' in request.referer:
        return HTTPFound(request.route_url(
            'detail',
            member_id=member.id))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(
    route_name='mail_mail_confirmation',
    permission='manage',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dashboard')
    ),
)
def mail_mail_conf(request):
    '''
    Send email to member to confirm her email address by clicking a link.

    Needed for applications that came in solely on paper
    and were digitalized/entered into DB by staff.
    '''
    member = request.validated_matchdict['member']

    send_mail_confirmation_mail(
        member,
        request.registry.settings['c3smembership.url'],
        request.registry.settings['c3smembership.notification_sender'],
        request.registry.get_mailer(request),
        request.registry.settings['testing.mail_to_console'])

    return get_dashboard_redirect(request, member.id)


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_acquisition_delete.pt',
    permission='manage',
    route_name='delete_afms')
def delete_afms(request):
    '''
    Delete a bunch of AfMs in one go.

    I wrote this while implementing mass import to ease development 8-)
    '''
    class DeleteAfMRange(colander.MappingSchema):
        """
        Schema for deleting a range of membership applications
        """
        first = colander.SchemaNode(
            colander.Integer(),
            title='first ID to delete'
        )
        last = colander.SchemaNode(
            colander.Integer(),
            title='last ID to delete'
        )
    schema = DeleteAfMRange()
    delete_range_form = deform.Form(
        schema,
        buttons=[deform.Button('delete_them', 'DELETE')]
    )
    if 'first' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = delete_range_form.validate(controls)
            _first = appstruct['first']
            _last = appstruct['last']
            # pylint: disable=superfluous-parens
            assert(_first < _last)
        except ValidationFailure, error:
            return {
                'resetform': error.render()
            }
        for i in range(_first, _last+1):
            C3sMember.delete_by_id(i)
        return HTTPFound(request.route_url('dashboard'))
    return {
        'delete_form': delete_range_form.render()
    }


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
    # pylint: disable=unused-argument

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
