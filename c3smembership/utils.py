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


country_codes = [
    ('AT', _(u'Austria')),
    ('BE', _(u'Belgium')),
    ('BG', _(u'Bulgaria')),
    ('CH', _(u'Switzerland')),
    ('CZ', _(u'Czech Republic')),
    ('DE', _(u'Germany')),
    ('DK', _(u'Denmark')),
    ('ES', _(u'Spain')),
    ('EE', _(u'Estonia')),
    ('FI', _(u'Finland')),
    ('FR', _(u'France')),
    ('GB', _(u'United Kingdom')),
    ('GR', _(u'Greece')),
    ('HU', _(u'Hungary')),
    ('HR', _(u'Croatia')),
    ('IE', _(u'Ireland')),
    ('IS', _(u'Iceland')),
    ('IT', _(u'Italy')),
    ('LT', _(u'Lithuania')),
    ('LI', _(u'Liechtenstein')),
    ('LV', _(u'Latvia')),
    ('LU', _(u'Luxembourg')),
    ('MT', _(u'Malta')),
    ('NL', _(u'Netherlands')),
    ('NO', _(u'Norway')),
    ('PL', _(u'Poland')),
    ('PT', _(u'Portugal')),
    ('SK', _(u'Slovakia')),
    ('SI', _(u'Slovenia')),
    ('SE', _(u'Sweden')),
    ('XX', _(u'other'))
]

locale_codes = [
    (u'de', _(u'Deutsch')),
    (u'en', _(u'Englisch')),
    (u'fr', _(u'Français')),
]


def generate_pdf(appstruct):
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
        here, "../pdftk/C3S-SCE-AFM-v12-20170822-de.pdf")
    declaration_pdf_en = os.path.join(
        here, "../pdftk/C3S-SCE-AFM-v12-20170822-en.pdf")

    if appstruct['locale'] == "de":
        pdf_to_be_used = declaration_pdf_de
    elif appstruct['locale'] == "en":
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
            'membership_type'] == u'normal' else '2'),
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


def generate_csv(appstruct):
    """
    returns a csv with the relevant data
    to ease import of new data sets
    """
    from datetime import date
    import unicodecsv

    csv = tempfile.TemporaryFile()
    csvw = unicodecsv.writer(csv, encoding='utf-8')
    fields = (
        date.today().strftime("%Y-%m-%d"),
        'pending...',
        appstruct['firstname'],
        appstruct['lastname'],
        appstruct['email'],
        appstruct['email_confirm_code'],
        appstruct['address1'],
        appstruct['address2'],
        appstruct['postcode'],
        appstruct['city'],
        appstruct['country'],
        u'investing' if appstruct[
            'membership_type'] == u'investing' else u'normal',
        appstruct['date_of_birth'],
        'j' if appstruct['member_of_colsoc'] == 'yes' else 'n',
        appstruct['name_of_colsoc'].replace(',', '|'),
        appstruct['num_shares'],
    )

    csvw.writerow(fields)

    csv.seek(0)
    return csv.readline()


def make_mail_body(appstruct):
    """
    construct a multiline string to be used as the emails body
    """
    unencrypted = u"""
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
        appstruct['date_of_submission'],
        appstruct['firstname'],
        appstruct['lastname'],
        appstruct['date_of_birth'],
        appstruct['email'],
        appstruct['email_confirm_code'],
        appstruct['address1'],
        appstruct['address2'],
        appstruct['postcode'],
        appstruct['city'],
        appstruct['country'],
        appstruct['membership_type'],
        appstruct['num_shares'],
        appstruct['member_of_colsoc'],
        appstruct['name_of_colsoc'],
    )
    return unencrypted


def accountant_mail(appstruct):
    """
    this function returns a message object for the mailer

    it consists of a mail body and an attachment attached to it
    """
    unencrypted = make_mail_body(appstruct)
    encrypted = encrypt_with_gnupg(unencrypted)

    message_recipient = appstruct['message_recipient']

    message = Message(
        subject="[C3S] Yes! a new member",
        sender="noreply@c3s.cc",
        recipients=[message_recipient],
        body=encrypted
    )
    csv_payload_encd = encrypt_with_gnupg(generate_csv(appstruct))

    attachment = Attachment(
        "C3S-SCE-AFM.csv.gpg", "application/gpg-encryption",
        csv_payload_encd)
    message.attach(attachment)

    return message
