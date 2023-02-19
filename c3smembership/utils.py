# -*- coding: utf-8  -*-
"""
Utilities for generating PDF and CSV files as well as sending emails.
"""

import subprocess
import tempfile
import time

from fdfgen import forge_fdf
from pyramid_mailer.message import (
    Message,
    Attachment,
)

from c3smembership.gnupg_encrypt import encrypt_with_gnupg
from c3smembership.presentation.i18n import _


country_codes = sorted(
    [
        ('AT', _('Austria')),
        ('BE', _('Belgium')),
        ('BG', _('Bulgaria')),
        ('CH', _('Switzerland')),
        ('CZ', _('Czech Republic')),
        ('DE', _('Germany')),
        ('DK', _('Denmark')),
        ('ES', _('Spain')),
        ('EE', _('Estonia')),
        ('FI', _('Finland')),
        ('FR', _('France')),
        ('GB', _('United Kingdom')),
        ('GR', _('Greece')),
        ('HU', _('Hungary')),
        ('HR', _('Croatia')),
        ('IE', _('Ireland')),
        ('IS', _('Iceland')),
        ('IT', _('Italy')),
        ('LT', _('Lithuania')),
        ('LI', _('Liechtenstein')),
        ('LV', _('Latvia')),
        ('LU', _('Luxembourg')),
        ('MT', _('Malta')),
        ('NL', _('Netherlands')),
        ('NO', _('Norway')),
        ('PL', _('Poland')),
        ('PT', _('Portugal')),
        ('SK', _('Slovakia')),
        ('SI', _('Slovenia')),
        ('SE', _('Sweden')),
        ('XX', _('other'))
    ],
    key=lambda x: x[1]
)

locale_codes = [
    ('de', _('Deutsch')),
    ('en', _('Englisch')),
    ('fr', _('Français')),
]


def generate_pdf(request, appstruct):
    """
    this function receives an appstruct
    (a datastructure received via formsubmission)
    and prepares and returns a PDF using pdftk
    """
    fdf_file = tempfile.NamedTemporaryFile()
    pdf_file = tempfile.NamedTemporaryFile()

    import os
    here = os.path.dirname(__file__)
    declaration_pdf_de = os.path.join(
        here, "../pdftk/C3S-SCE-AFM-v14-20210630-de.pdf")
    declaration_pdf_en = os.path.join(
        here, "../pdftk/C3S-SCE-AFM-v14-20210630-en.pdf")

    if request.locale_name == "de":
        pdf_to_be_used = declaration_pdf_de
    elif request.locale_name == "en":
        pdf_to_be_used = declaration_pdf_en
    else:  # pragma: no cover
        pdf_to_be_used = declaration_pdf_en

    dob_ = time.strptime(str(appstruct['date_of_birth']), '%Y-%m-%d')
    dob = time.strftime("%d.%m.%Y", dob_)
    dos = str(appstruct['date_of_submission'])
    amount = str(appstruct['num_shares'] * 50)

    from datetime import datetime

    fields = [
        ('firstname', appstruct['firstname']),
        ('lastname', appstruct['lastname']),
        ('streetNo', appstruct['address1']),
        ('address2', appstruct['address2']),
        ('postcode', appstruct['postcode']),
        ('town', appstruct['city']),
        ('email', appstruct['email']),
        ('country', appstruct['country']),
        ('MembershipType', '1' if appstruct[
            'membership_type'] == 'normal' else '2'),
        ('numshares', str(appstruct['num_shares'])),
        ('dateofbirth', dob),
        ('submitted', dos),
        ('generated', str(datetime.now())),
        ('code', appstruct['email_confirm_code']),
        ('code2', appstruct['email_confirm_code']),  # for page 2
        ('amount', amount),  # for page 2
    ]

    fdf = forge_fdf("", fields, [], [], [])

    fdf_file.write(fdf)
    fdf_file.seek(0)

    subprocess.call(
        [
            'pdftk',
            pdf_to_be_used,  # input pdf with form fields
            'fill_form', fdf_file.name,  # fill in values
            'output', pdf_file.name,  # output file
            'flatten',  # make form read-only
        ]
    )

    pdf_file.seek(0)

    from pyramid.response import Response
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)  # rewind to beginning
    response.app_iter = open(pdf_file.name, "r")

    return response


def generate_csv(member):
    """
    returns a csv with the relevant data
    to ease import of new data sets
    """
    from datetime import date
    import csv

    csvf = tempfile.TemporaryFile()
    csvw = csv.writer(csvf, encoding='utf-8')
    fields = (
        date.today().strftime("%Y-%m-%d"),
        'pending...',
        member.firstname,
        member.lastname,
        member.email,
        member.email_confirm_code,
        member.address1,
        member.address2,
        member.postcode,
        member.city,
        member.country,
        'investing' if member.membership_type == 'investing' else 'normal',
        member.date_of_birth,
        'j' if member.member_of_colsoc == 'yes' else 'n',
        member.name_of_colsoc.replace(',', '|'),
        member.num_shares,
    )

    csvw.writerow(fields)

    csvf.seek(0)
    return csvf.readline()


def make_mail_body(member):
    """
    construct a multiline string to be used as the emails body
    """
    unencrypted = """
Yay!
we got a membership application through the form: \n
date of submission:             {}
first name:                     {}
last name:                      {}
date of birth:                  {}
email:                          {}
email confirmation code:        {}
street/no                       {}
address cont'd                  {}
postcode:                       {}
city:                           {}
country:                        {}
membership type:                {}
number of shares                {}

member of coll. soc.:           {}
  name of coll. soc.:           {}

that's it.. bye!""". \
    format(
        member.date_of_submission,
        member.firstname,
        member.lastname,
        member.date_of_birth,
        member.email,
        member.email_confirm_code,
        member.address1,
        member.address2,
        member.postcode,
        member.city,
        member.country,
        member.membership_type,
        member.num_shares,
        member.member_of_colsoc,
        member.name_of_colsoc,
    )
    return unencrypted


def create_accountant_mail(member, sender, recipients):
    """
    Create an email message information the accountant about the new
    membership application.
    """
    unencrypted = make_mail_body(member)
    encrypted = encrypt_with_gnupg(unencrypted)

    message = Message(
        subject="[C3S] Yes! a new member",
        sender=sender,
        recipients=recipients,
        body=encrypted
    )
    csv_payload_encd = encrypt_with_gnupg(generate_csv(member))

    attachment = Attachment(
        "C3S-SCE-AFM.csv.gpg",
        "application/gpg-encryption",
        csv_payload_encd)
    message.attach(attachment)
    return message


def send_accountant_mail(request, member):
    """
    Send an GPG encrypted email to the accountant informing about the new
    membership application.
    """
    mailer = request.registry.get_mailer(request)
    try:
        the_mail = create_accountant_mail(
            member,
            request.registry.settings['c3smembership.notification_sender'],
            [request.registry.settings['c3smembership.status_receiver']])
        if 'true' in request.registry.settings['testing.mail_to_console']:
            # pylint: disable=superfluous-parens
            print((the_mail.body))
        else:
            mailer.send(the_mail)
    except:
        mail = Message(
            subject=_("[yes][ALERT] check the logs!"),
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[request.registry.settings[
                'c3smembership.status_receiver']],
            body="""
A failure occurred at {}. A notification email could not be sent.
Maybe gnupg failed and a key might be expired.
            """.format(request.registry.settings['c3smembership.url']))
        mailer.send(mail)
