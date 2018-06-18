# -*- coding: utf-8 -*-
"""
This module holds views for accountants to do accounting stuff.

- Log In or Log Out
- Administer Applications for Membership on the Dashboard
- Check reception of signature, send reception confirmation or reminder mails
- Check reception of payment, send reception confirmation or reminder mails
- Check application details
- Deletion of applications
- ReGenerate a PDF for an application
"""

import logging

from datetime import (
    datetime,
    date,
)
from decimal import Decimal
from types import NoneType

import deform
from deform import ValidationFailure
from pyramid_mailer.message import Message
from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
)
from pyramid.url import route_url
from pyramid.view import view_config

from c3smembership.mail_utils import (
    make_payment_confirmation_email,
    send_message,
)
from c3smembership.mail_reminders_util import (
    make_signature_reminder_email,
    make_payment_reminder_email,
)
from c3smembership.models import (
    C3sMember,
    C3sStaff,
    Dues15Invoice,
    Dues16Invoice,
    Dues17Invoice,
    Dues18Invoice,
)
from c3smembership.presentation.i18n import _
from c3smembership.presentation.schemas.accountant_login import (
    AccountantLogin
)
from c3smembership.presentation.views.dashboard import get_dashboard_redirect
from c3smembership.utils import generate_pdf


DEBUG = False
LOG = logging.getLogger(__name__)


@view_config(renderer='templates/login.pt',
             route_name='login')
def accountants_login(request):
    """
    This view lets accountants log in (using a login form).

    If a person is already logged in, she is forwarded to the dashboard.
    """
    logged_in = authenticated_userid(request)

    LOG.info("login by %s", logged_in)

    if logged_in is not None:
        return get_dashboard_redirect(request)

    form = deform.Form(
        AccountantLogin(),
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
    )

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure, e_validation_failure:
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'form': e_validation_failure.render()}

        # get user and check pw...
        login = appstruct['login']
        password = appstruct['password']

        try:
            checked = C3sStaff.check_password(login, password)
        except AttributeError:  # pragma: no cover
            checked = False
        if checked:
            LOG.info("password check for %s: good!", login)
            headers = remember(request, login)
            LOG.info("logging in %s", login)
            return HTTPFound(
                request.route_url(
                    'dashboard'),
                headers=headers)
        else:
            LOG.info("password check: failed for %s.", login)
    else:
        request.session.pop('message_above_form')

    html = form.render()
    return {'form': html, }


@view_config(permission='manage',
             route_name='switch_sig')
def switch_sig(request):
    """
    This view lets accountants switch an applications signature status
    once their signature has arrived.

    Note:
        Expects the object request.registry.membership_application to implement
    """
    member_id = request.matchdict['memberid']

    membership_application = request.registry.membership_application
    signature_received = membership_application.get_signature_status(member_id)
    new_signature_received = not signature_received
    membership_application.set_signature_status(
        member_id,
        new_signature_received)

    LOG.info(
        "signature status of member.id %s changed by %s to %s",
        member_id,
        request.user.login,
        new_signature_received
    )

    if 'dashboard' in request.referrer:
        return get_dashboard_redirect(request, member_id)
    else:
        return HTTPFound(
            request.route_url(
                'detail',
                memberid=member_id,
                _anchor='membership_info'
            )
        )


@view_config(permission='manage',
             route_name='delete_entry')
def delete_entry(request):
    """
    This view lets accountants delete datasets (e.g. doublettes, test entries).
    """

    deletion_confirmed = (request.params.get('deletion_confirmed', '0') == '1')
    redirection_view = request.params.get('redirect', 'dashboard')
    LOG.info('redirect to: ' + str(redirection_view))

    if deletion_confirmed:
        memberid = request.matchdict['memberid']
        member = C3sMember.get_by_id(memberid)
        member_lastname = member.lastname
        member_firstname = member.firstname

        C3sMember.delete_by_id(member.id)
        LOG.info(
            "member.id %s was deleted by %s",
            member.id,
            request.user.login,
        )
        message = "member.id %s was deleted" % member.id
        request.session.flash(message, 'messages')

        msgstr = u'Member with id {0} \"{1}, {2}\" was deleted.'
        return HTTPFound(
            request.route_url(
                redirection_view,
                _query={'message': msgstr.format(
                    memberid,
                    member_lastname,
                    member_firstname)},
                _anchor='member_{id}'.format(id=str(memberid))
            )
        )
    else:
        return HTTPFound(
            request.route_url(
                redirection_view,
                _query={'message': (
                    'Deleting the member was not confirmed'
                    ' and therefore nothing has been deleted.')}
            )
        )


@view_config(permission='manage',
             route_name='switch_pay')
def switch_pay(request):
    """
    This view lets accountants switch a member applications payment status
    once their payment has arrived.
    """
    member_id = request.matchdict['memberid']

    membership_application = request.registry.membership_application
    payment_received = membership_application.get_payment_status(member_id)
    new_payment_received = not payment_received
    membership_application.set_payment_status(
        member_id,
        new_payment_received)

    LOG.info(
        "payment info of member.id %s changed by %s to %s",
        member_id,
        request.user.login,
        new_payment_received
    )
    if 'dashboard' in request.referrer:
        return get_dashboard_redirect(request, member_id)
    else:
        return HTTPFound(
            request.route_url(
                'detail',
                memberid=member_id,
                _anchor='membership_info')
        )


def get_member_details(request, member):
    """
    Gets the member details.
    """
    invoices15 = Dues15Invoice.get_by_membership_no(member.membership_number)
    invoices16 = Dues16Invoice.get_by_membership_no(member.membership_number)
    invoices17 = Dues17Invoice.get_by_membership_no(member.membership_number)
    invoices18 = Dues18Invoice.get_by_membership_no(member.membership_number)
    shares = request.registry.share_information.get_member_shares(
        member.membership_number)

    return {
        'today': date.today().strftime('%Y-%m-%d'),
        'D': Decimal,
        'member': member,
        'shares': shares,
        'invoices15': invoices15,
        'invoices16': invoices16,
        'invoices17': invoices17,
        'invoices18': invoices18,
    }


@view_config(renderer='templates/detail.pt',
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
            'message_to_staff'
        )
        return HTTPFound(  # back to base
            request.route_url('toolbox'))

    return get_member_details(request, member)


@view_config(renderer='templates/detail.pt',
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
            'message_to_staff'
        )
        return HTTPFound(  # back to base
            request.route_url('toolbox'))

    return get_member_details(request, member)


@view_config(permission='view',
             route_name='logout')
def logout_view(request):
    """
    Is used to log a user/staffer off. "forget"
    """
    request.session.invalidate()
    request.session.flash(u'Logged out successfully.')
    headers = forget(request)
    return HTTPFound(
        location=route_url('login', request),
        headers=headers
    )


@view_config(permission='manage',
             route_name='regenerate_pdf')
def regenerate_pdf(request):
    """
    Staffers can regenerate an applicants PDF and send it to her.
    """
    code = request.matchdict['code']
    member = C3sMember.get_by_code(code)

    if member is None:
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
    return generate_pdf(appstruct)


@view_config(permission='manage',
             route_name='mail_sig_confirmation')
def mail_signature_confirmation(request):
    """
    Send a mail to a membership applicant
    informing her about reception of signature.
    """
    member_id = request.matchdict['memberid']

    membership_application = request.registry.membership_application
    membership_application.mail_signature_confirmation(member_id, request)

    if 'detail' in request.referrer:
        return HTTPFound(request.route_url(
            'detail',
            memberid=member_id))
    else:
        return get_dashboard_redirect(request, member_id)


@view_config(permission='manage',
             route_name='mail_pay_confirmation')
def mail_payment_confirmation(request):
    """
    Send a mail to a membership applicant
    informing her about reception of payment.
    """
    member = request.registry.member_information.get_member_by_id(
        request.matchdict['member_id'])

    email_subject, email_body = make_payment_confirmation_email(member)
    message = Message(
        subject=email_subject,
        sender='yes@c3s.cc',
        recipients=[member.email],
        body=email_body,
    )
    send_message(request, message)

    member.payment_confirmed = True
    member.payment_confirmed_date = datetime.now()
    if 'detail' in request.referrer:
        return HTTPFound(request.route_url(
            'detail',
            memberid=member.id))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(permission='manage',
             route_name='mail_sig_reminder')
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
    member_id = request.matchdict['memberid']
    member = C3sMember.get_by_id(member_id)
    if isinstance(member, NoneType):
        request.session.flash(
            'that member was not found! (id: {})'.format(member_id),
            'messages'
        )
        return get_dashboard_redirect(request, member.id)

    email_subject, email_body = make_signature_reminder_email(member)
    message = Message(
        subject=email_subject,
        sender='office@c3s.cc',
        recipients=[member.email],
        body=email_body
    )
    send_message(request, message)

    try:
        member.sent_signature_reminder += 1
    except TypeError:
        # if value was None (after migration of DB schema)
        member.sent_signature_reminder = 1
    member.sent_signature_reminder_date = datetime.now()
    if 'detail' in request.referrer:
        return HTTPFound(request.route_url(
            'detail',
            memberid=request.matchdict['memberid']))
    else:
        return get_dashboard_redirect(request, member.id)


@view_config(permission='manage',
             route_name='mail_pay_reminder')
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
    member = request.registry.member_information.get_member_by_id(
        request.matchdict['memberid'])

    email_subject, email_body = make_payment_reminder_email(member)
    message = Message(
        subject=email_subject,
        sender='office@c3s.cc',
        recipients=[member.email],
        body=email_body
    )
    send_message(request, message)

    try:  # if value is int
        member.sent_payment_reminder += 1
    except TypeError:  # pragma: no cover
        # if value was None (after migration of DB schema)
        member.sent_payment_reminder = 1
    member.sent_payment_reminder_date = datetime.now()
    if 'detail' in request.referrer:
        return HTTPFound(request.route_url(
            'detail',
            memberid=request.matchdict['memberid']))
    else:
        return get_dashboard_redirect(request, member.id)
