# -*- coding: utf-8 -*-
"""
Compiles email texts for payment confirmation and signature confirmation
emails.
"""

import os

from pyramid_mailer import get_mailer


LOCALE_DEFINITIONS = {
    'de': {
        'date_format': '%d. %m. %Y',
    },
    'en': {
        'date_format': '%d %b %Y',
    },
}


def get_locale(locale):
    return locale if locale in LOCALE_DEFINITIONS else 'en'


def get_template_text(template_name, locale):
    return open(
        '{base_path}/templates/mail/{template_name}_{locale}.txt'.format(
            base_path=os.path.dirname(__file__),
            template_name=template_name,
            locale=get_locale(locale)),
        'rb').read().decode('utf-8')


def get_salutation(member):
    if member.is_legalentity:
        # for legal entites the firstname attribute contains the name of the
        # contact person of the legal entity while the lastname attribute
        # contains the legal entity's name
        return member.firstname
    else:
        return u'{first_name} {last_name}'.format(
            first_name=member.firstname,
            last_name=member.lastname)


def format_date(date, locale):
    return date.strftime(
        LOCALE_DEFINITIONS[get_locale(locale)]['date_format'])


def get_email_footer(locale):
    return get_template_text('email_footer', locale)


def make_membership_certificate_email(request, member):
    """
    Gets an email subject and body to delivery a link to the membership
    certificate PDF.
    """
    subject = get_template_text(
        'membership_certificate_subject', member.locale)
    if member.is_legalentity:
        body = get_template_text(
            'membership_certificate_legalentity_body',
            member.locale
        ).format(
            salutation=get_salutation(member),
            legal_entity_name=member.lastname,
            url=request.route_url(
                'certificate_pdf',
                member_id=member.id,
                name=member.get_url_safe_name(),
                token=member.certificate_token),
            footer=get_email_footer(member.locale))
    else:
        body = get_template_text(
            'membership_certificate_naturalperson_body',
            member.locale
        ).format(
            salutation=get_salutation(member),
            url=request.route_url(
                'certificate_pdf',
                member_id=member.id,
                name=member.get_url_safe_name(),
                token=member.certificate_token),
            footer=get_email_footer(member.locale))
    return (subject, body)


def make_payment_confirmation_email(member):
    """
    Gets an email subject and body to confirm the reception of the payment
    for shares.
    """
    return (
        get_template_text('payment_confirmation_subject', member.locale),
        get_template_text('payment_confirmation_body', member.locale).format(
            num_shares=member.num_shares,
            sum_shares=member.num_shares * 50,
            salutation=get_salutation(member),
            footer=get_email_footer(member.locale)))


def make_signature_confirmation_email(member):
    """
    An email body to confirm reception of signature
    """
    return (
        get_template_text('signature_confirmation_subject', member.locale),
        get_template_text('signature_confirmation_body', member.locale).format(
            num_shares=member.num_shares,
            sum_shares=member.num_shares * 50,
            salutation=get_salutation(member),
            footer=get_email_footer(member.locale)))


def send_message(request, message):
    """
    Sends a message through the mailer.

    In debugging mode the message will be written to the console.
    """
    if 'true' in request.registry.settings['testing.mail_to_console']:
        print(u'Sender: ' + unicode(message.sender))
        print(u'Receipients: ' + unicode(message.recipients))
        print(u'Subject: ' + unicode(message.subject))
        print(message.body.encode('utf-8'))
    else:
        mailer = None
        if hasattr(request.registry, 'get_mailer'):
            # For dependency injection
            mailer = request.registry.get_mailer(request)
        else:
            # For legacy
            # TODO: Remove long-term
            mailer = get_mailer(request)
        mailer.send(message)
