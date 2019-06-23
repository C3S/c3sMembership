# -*- coding: utf-8 -*-
"""
This module holds code for Membership Dues (2017 edition).

* Send email to a member:

   - request transferral of membership dues.
   - also send link to invoice PDF.

* Produce an invoice PDF when member clicks her invoice link.
* Batch-send email to n members.
* When dues transfer arrives, book it to member.
* When member asks for reduction of dues fee, let staff handle it:

   - set a new reduced amount
   - send email with update: reversal invoice and new invoice
"""
from datetime import (
    datetime,
    date,
)
from decimal import Decimal as D
import math
import os
import shutil
import subprocess
import tempfile

from pyramid.httpexceptions import HTTPFound
from pyramid_mailer.message import Message
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues17invoice import Dues17Invoice

from c3smembership.mail_utils import send_message
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)
from c3smembership.presentation.views.dues_texts import (
    make_dues17_invoice_email,
    make_dues_invoice_investing_email,
    make_dues_invoice_legalentity_email,
    make_dues17_reduction_email,
    make_dues_exemption_email,
)
from c3smembership.tex_tools import TexTools


DEBUG = False
LOGGING = True

if LOGGING:  # pragma: no cover
    import logging
    LOG = logging.getLogger(__name__)


def make_random_string():
    """
    a random string used as dues token
    """
    import random
    import string
    return u''.join(
        random.choice(
            string.ascii_uppercase
        ) for x in range(10))


def calculate_partial_dues17(member):
    """
    helper function: calculate..

    * codified start quarter (q1, q2, q3, q4) and
    * dues

    depending on members entry date
    """
    if member.membership_date >= date(2018, 1, 1):
        raise ValueError('Member is not applicable for dues 2017.')

    if member.membership_date < date(2017, 4, 1):
        # first quarter of 2017 or earlier
        start = u'q1_2017'
        amount = D('50')
    elif member.membership_date < date(2017, 7, 1):
        # second quarter of 2017
        start = u'q2_2017'
        amount = D('37.50')
    elif member.membership_date < date(2017, 10, 1):
        # third quarter of 2017
        start = u'q3_2017'
        amount = D('25')
    elif member.membership_date >= date(2017, 10, 1):
        # third quarter of 2017
        start = u'q4_2017'
        amount = D('12.50')
    return (start, amount)


def string_start_quarter_dues17(member):
    """
    helper function: produce translated string for quarter of entry date
    depending on members locale
    """
    loc = member.locale
    result = u''
    if 'q1_2017' in member.dues17_start:  # first quarter of 2017 or earlier
        result = u"für das ganze Jahr" if 'de' in loc else "for the whole year"
    elif 'q2_2017' in member.dues17_start:  # second quarter of 2017
        result = u"ab Quartal 2" if 'de' in loc else u"from 2nd quarter"
    elif 'q3_2017' in member.dues17_start:  # third quarter of 2017
        result = u"ab Quartal 3" if 'de' in loc else u"from 3rd quarter"
    elif 'q4_2017' in member.dues17_start:  # third quarter of 2017
        result = u"ab Quartal 4" if 'de' in loc else u"from 4th quarter"
    return result


@view_config(
    permission='manage',
    route_name='send_dues17_invoice_email')
def send_dues17_invoice_email(request, m_id=None):
    """
    Send email to a member to prompt her to pay the membership dues.
    - For normal members, also send link to invoice.
    - For investing members that are legal entities,
      ask for additional support depending on yearly turnover.

    This view function works both if called via URL, e.g. /dues_invoice/123
    and if called as a function with a member id as parameter.
    The latter is useful for batch processing.

    When this function is used for the first time for one member,
    some database fields are filled:
    - Invoice number
    - Invoice amount (calculated from date of membership approval by the board)
    - Invoice token
    Also, the database table of invoices (and cancellations) is appended.

    If this function gets called the second time for a member,
    no new invoice is produced, but the same mail sent again.
    """
    # either we are given a member id via url or function parameter
    try:  # view was called via http/s
        member_id = request.matchdict['member_id']
        batch = False
    except KeyError:  # ...or was called as function with parameter (see batch)
        member_id = m_id
        batch = True

    try:  # get member from DB
        member = C3sMember.get_by_id(member_id)
        assert(member is not None)
    except AssertionError:
        if not batch:
            request.session.flash(
                "member with id {} not found in DB!".format(member_id),
                'warning')
            return HTTPFound(request.route_url('toolbox'))

    # sanity check:is this a member?
    try:
        assert(member.membership_accepted)  # must be accepted member!
    except AssertionError:
        request.session.flash(
            "member {} not accepted by the board!".format(member_id),
            'warning')
        return HTTPFound(request.route_url('toolbox'))

    if 'normal' not in member.membership_type and \
            'investing' not in member.membership_type:
        request.session.flash(
            'The membership type of member {0} is not specified! The '
            'membership type must either be "normal" or "investing" in order '
            'to be able to send an invoice email.'.format(member.id),
            'warning')
        return get_memberhip_listing_redirect(request)
    if member.membership_date >= date(2018,1,1) or ( \
                member.membership_loss_date is not None
                and
                member.membership_loss_date < date(2017,1,1)
            ):
        request.session.flash(
            'Member {0} was not a member in 2017. Therefore, you cannot send '
            'an invoice for 2017.'.format(member.id),
            'warning')
        return get_memberhip_listing_redirect(request)

    # check if invoice no already exists.
    #     if yes: just send that email again!
    #     also: offer staffers to cancel this invoice

    if member.dues17_invoice is True:
        invoice = Dues17Invoice.get_by_invoice_no(member.dues17_invoice_no)
        member.dues17_invoice_date = datetime.now()

    else:  # if no invoice already exists:
        # make dues token and ...
        randomstring = make_random_string()
        # check if dues token is already used
        while (Dues17Invoice.check_for_existing_dues17_token(randomstring)):
            # create a new one, if the new one already exists in the database
            randomstring = make_random_string()  # pragma: no cover

        # prepare invoice number
        try:
            # either we already have an invoice number for that client...
            invoice_no = member.dues17_invoice_no
            assert invoice_no is not None
        except AssertionError:
            # ... or we create a new one and save it
            # get max invoice no from db
            max_invoice_no = Dues17Invoice.get_max_invoice_no()
            # use the next free number, save it to db
            new_invoice_no = int(max_invoice_no) + 1
            DBSession.flush()  # save dataset to DB

        # calculate dues amount (maybe partial, depending on quarter)
        dues_start, dues_amount = calculate_partial_dues17(member)

        # now we have enough info to update the member info
        # and persist invoice info for bookkeeping
        # store some info in DB/member table
        member.dues17_invoice = True
        member.dues17_invoice_no = new_invoice_no  # irrelevant for investing
        member.dues17_invoice_date = datetime.now()
        member.dues17_token = randomstring
        member.dues17_start = dues_start

        if 'normal' in member.membership_type:  # only for normal members
            member.set_dues17_amount(dues_amount)
            # store some more info about invoice in invoice table
            invoice = Dues17Invoice(
                invoice_no=member.dues17_invoice_no,
                invoice_no_string=(
                    u'C3S-dues2017-' + str(member.dues17_invoice_no).zfill(4)),
                invoice_date=member.dues17_invoice_date,
                invoice_amount=u'' + str(member.dues17_amount),
                member_id=member.id,
                membership_no=member.membership_number,
                email=member.email,
                token=member.dues17_token,
            )
            DBSession.add(invoice)
        DBSession.flush()

    # now: prepare that email
    # only normal (not investing) members *have to* pay the dues.
    # only the normal members get an invoice link and PDF produced for them.
    # only investing legalentities are asked for more support.
    if 'investing' not in member.membership_type:
        start_quarter = string_start_quarter_dues17(member)
        invoice_url = (
            request.route_url(
                'make_dues17_invoice_no_pdf',
                email=member.email,
                code=member.dues17_token,
                i=str(member.dues17_invoice_no).zfill(4)
            )
        )
        email_subject, email_body = make_dues17_invoice_email(
            member,
            invoice,
            invoice_url,
            start_quarter)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[member.email],
            body=email_body,
        )
    elif 'investing' in member.membership_type:
        if member.is_legalentity:
            email_subject, email_body = \
                make_dues_invoice_legalentity_email(member)
        else:
            email_subject, email_body = \
                make_dues_invoice_investing_email(member)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings[
                'c3smembership.notification_sender'],
            recipients=[member.email],
            body=email_body,
        )

    # print to console or send mail
    if 'true' in request.registry.settings['testing.mail_to_console']:
        print(message.body.encode('utf-8'))  # pragma: no cover
    else:
        send_message(request, message)

    # now choose where to redirect
    if 'detail' in request.referrer:
        return HTTPFound(
            request.route_url(
                'detail',
                memberid=member.id) +
            '#dues17')
    if 'toolbox' in request.referrer:
        return HTTPFound(request.route_url('toolbox'))
    else:
        return get_memberhip_listing_redirect(request, member.id)


@view_config(
    permission='manage',
    route_name='send_dues17_invoice_batch'
)
def send_dues17_invoice_batch(request):
    """
    Send dues invoice to n members at the same time (batch processing).

    The number (n) is configurable, defaults to 5.
    """
    try:  # how many to process?
        number = int(request.matchdict['number'])
    except KeyError:
        number = 5
    if 'submit' in request.POST:
        try:
            number = int(request.POST['number'])
        except KeyError:  # pragma: no cover
            number = 5

    invoicees = C3sMember.get_dues17_invoicees(number)

    if len(invoicees) == 0:
        request.session.flash('no invoicees left. all done!',
                              'success')
        return HTTPFound(request.route_url('toolbox'))

    emails_sent = 0
    ids_sent = []
    request.referrer = 'toolbox'

    for member in invoicees:
        send_dues17_invoice_email(request=request, m_id=member.id)
        emails_sent += 1
        ids_sent.append(member.id)

    request.session.flash(
        "sent out {} mails (to members with ids {})".format(
            emails_sent, ids_sent),
        'success')

    return HTTPFound(request.route_url('toolbox'))


@view_config(route_name='make_dues17_invoice_no_pdf')
def make_dues17_invoice_no_pdf(request):
    """
    Create invoice PDFs on-the-fly.

    This view checks supplied information (in URL) against info in database
    and returns
    - an error message OR
    - a PDF as receipt

    === ===========================================================
    URL http://app:port/dues_invoice_no/EMAIL/CAQJGCGUFW/C3S-dues17-0001.pdf
    === ===========================================================

    """
    token = request.matchdict['code']
    invoice_number = request.matchdict['i']

    try:
        member = C3sMember.get_by_dues17_token(token)
        assert member is not None
        assert member.dues17_token == token
    except AssertionError:
        request.session.flash(
            u"This member and token did not match!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    try:
        invoice = Dues17Invoice.get_by_invoice_no(
            invoice_number.lstrip('0'))
        assert invoice is not None
    except AssertionError:
        request.session.flash(
            u"No invoice found!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # sanity check: invoice token must match with token
    try:
        assert(invoice.token == token)
    except AssertionError:
        request.session.flash(
            u"Token did not match!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # sanity check: invoice must not be reversal
    try:
        assert(not invoice.is_reversal)
    except AssertionError:
        request.session.flash(
            u"Token did not match!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # return a pdf file
    pdf_file = make_invoice_pdf_pdflatex(member, invoice)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)  # rewind to beginning
    response.app_iter = open(pdf_file.name, "r")
    return response


def get_dues17_invoice_archive_path():
    invoice_archive_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../../invoices/'))
    if not os.path.isdir(invoice_archive_path):
        os.makedirs(invoice_archive_path)
    return invoice_archive_path


def get_dues17_archive_invoice_filename(invoice):
    return os.path.join(
        get_dues17_invoice_archive_path(),
        '{0}.pdf'.format(invoice.invoice_no_string))


def archive_dues17_invoice(pdf_file, invoice):
    invoice_archive_filename = get_dues17_archive_invoice_filename(
        invoice)
    if not os.path.isfile(invoice_archive_filename):
        shutil.copyfile(
            pdf_file.name,
            invoice_archive_filename
        )


def get_dues17_archive_invoice(invoice):
    invoice_archive_filename = get_dues17_archive_invoice_filename(
        invoice)
    if os.path.isfile(invoice_archive_filename):
        return open(invoice_archive_filename, 'rb')
    else:
        return None


def make_invoice_pdf_pdflatex(member, invoice=None):
    """
    This function uses pdflatex to create a PDF
    as receipt for the members membership dues.

    default output is the current invoice.
    if i_no is suplied, the relevant invoice number is produced
    """

    dues17_archive_invoice = get_dues17_archive_invoice(invoice)
    if dues17_archive_invoice is not None:
        return dues17_archive_invoice

    # directory of pdf and tex files
    pdflatex_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../../certificate/'
        ))

    # pdf backgrounds
    pdf_backgrounds = {
        'blank': pdflatex_dir + '/' + 'Urkunde_Hintergrund_blank.pdf',
    }

    # latex templates
    latex_templates = {
        # 'generic': pdflatex_dir + '/' + 'membership_dues_receipt.tex',
        'generic': pdflatex_dir + '/' + 'dues17_invoice_de.tex',
        'generic_en': pdflatex_dir + '/' + 'dues17_invoice_en.tex',
    }

    # choose background and template
    background = 'blank'
    template_name = 'generic' if 'de' in member.locale else 'generic_en'

    # pick background and template
    bg_pdf = pdf_backgrounds[background]
    tpl_tex = latex_templates[template_name]

    # pick temporary file for pdf
    receipt_pdf = tempfile.NamedTemporaryFile(prefix='invoice_', suffix='.pdf')

    (path, filename) = os.path.split(receipt_pdf.name)
    filename = os.path.splitext(filename)[0]

    # on invoice, print start quarter or "reduced". prepare string:
    if (
            not invoice.is_reversal and
            invoice.is_altered and
            invoice.preceding_invoice_no is not None):
        is_altered_str = u'angepasst' if (
            'de' in member.locale) else u'altered'

    if invoice is not None:
        # use invoice no from URL
        invoice_no = str(invoice.invoice_no).zfill(4)
        invoice_date = invoice.invoice_date.strftime('%d. %m. %Y')
    else:  # pragma: no cover
        # this branch is deprecated, because we always supply an invoice number
        # use invoice no from member record
        invoice_no = str(member.dues17_invoice_no).zfill(4)
        invoice_date = member.dues17_invoice_date

    dues15_balance = D('0.0')
    dues16_balance = D('0.0')
    dues17_balance = D('0.0')

    if not math.isnan(member.dues15_balance):
        dues15_balance = member.dues15_balance
    if not math.isnan(member.dues16_balance):
        dues16_balance = member.dues16_balance
    if not math.isnan(member.dues17_balance):
        dues17_balance = member.dues17_balance

    # set variables for tex command
    tex_vars = {
        'personalFirstname': member.firstname,
        'personalLastname': member.lastname,
        'personalAddressOne': member.address1,
        'personalAddressTwo': member.address2,
        'personalPostCode': member.postcode,
        'personalCity': member.city,
        'personalMShipNo': unicode(member.membership_number),
        'invoiceNo': str(invoice_no).zfill(4),  # leading zeroes!
        'invoiceDate': invoice_date,
        'account': unicode(-dues15_balance - dues16_balance \
                - dues17_balance),
        'duesStart':  is_altered_str if (
            invoice.is_altered) else string_start_quarter_dues17(member),
        'duesAmount': unicode(invoice.invoice_amount),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    # generate tex command for pdflatex
    tex_cmd = u''
    for key, val in iter(tex_vars.items()):
        tex_cmd += '\\newcommand{\\%s}{%s}' % (key, TexTools.escape(val))
    tex_cmd += '\\input{%s}' % tpl_tex
    tex_cmd = u'"'+tex_cmd+'"'

    # make latex show ß correctly in pdf:
    tex_cmd = tex_cmd.replace(u'ß', u'\\ss{}')

    # XXX: try to find out, why utf-8 doesn't work on debian
    # TODO: Handle any return code not equal to zero
    subprocess.call(
        [
            'pdflatex',
            '-jobname', filename,
            '-output-directory', path,
            '-interaction', 'nonstopmode',
            '-halt-on-error',
            tex_cmd.encode('latin_1')
        ],
        stdout=open(os.devnull, 'w'),  # hide output
        stderr=subprocess.STDOUT,
        cwd=pdflatex_dir
    )

    # cleanup
    aux = os.path.join(path, filename + '.aux')
    if os.path.isfile(aux):
        os.unlink(aux)

    archive_dues17_invoice(receipt_pdf, invoice)

    return receipt_pdf


@view_config(
    route_name='dues17_listing',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues17_list.pt'
)
def dues17_listing(request):
    """
    a listing of all invoices for the 2017 dues run.
    shall show both active/valid and cancelled/invalid invoices.
    """
    # get them all from the DB
    dues17_invoices = Dues17Invoice.get_all()

    return {
        'count': len(dues17_invoices),
        '_today': date.today(),
        'invoices': dues17_invoices,
    }


@view_config(
    route_name='dues17_reduction',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues17_list.pt'
)
def dues17_reduction(request):
    """
    reduce a members dues upon valid request to do so.

    * change payable amount for member
    * cancel old invoice by issuing a cancellation
    * issue a new invoice with the new amount (if new amount != 0)

    this will only work for *normal* members.
    """
    # member: sanity checks
    try:
        member_id = request.matchdict['member_id']
        member = C3sMember.get_by_id(member_id)  # is in database
        assert member.membership_accepted  # is a member
        assert 'investing' not in member.membership_type  # is normal member
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            u"No member OR not accepted OR not normal member",
            'dues17_message_to_staff'  # message queue for staff
        )
        return HTTPFound(

            request.route_url('detail', memberid=member.id) + '#dues17')

    # sanity check: the given amount is a positive decimal
    try:
        reduced_amount = D(request.POST['amount'])
        assert not reduced_amount.is_signed()
        if DEBUG:
            print("DEBUG: reduction to {}".format(reduced_amount))
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            (u"Invalid amount to reduce to: '{}' "
             u"Use the dot ('.') as decimal mark, e.g. '23.42'".format(
                 request.POST['amount'])),
            'dues17_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    if DEBUG:
        print("DEBUG: member.dues17_amount: {}".format(
            member.dues17_amount))
        print("DEBUG: type(member.dues17_amount): {}".format(
            type(member.dues17_amount)))
        print("DEBUG: member.dues17_reduced: {}".format(
            member.dues17_reduced))
        print("DEBUG: member.dues17_amount_reduced: {}".format(
            member.dues17_amount_reduced))
        print("DEBUG: type(member.dues17_amount_reduced): {}".format(
            type(member.dues17_amount_reduced)))

    # The hidden input 'confirmed' must have the value 'yes' which is set by
    # the confirmation dialog.
    reduction_confirmed = request.POST['confirmed']
    if reduction_confirmed != 'yes':
        request.session.flash(
            u'Die Reduktion wurde nicht bestätigt.',
            'dues17_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    # check the reduction amount: same as default calculated amount?
    if (not member.dues17_reduced and
            member.dues17_amount == reduced_amount):
        request.session.flash(
            u"Dieser Beitrag ist der default-Beitrag!",
            'dues17_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    if (member.dues17_reduced and
            reduced_amount == member.dues17_amount_reduced):
        request.session.flash(
            u"Auf diesen Beitrag wurde schon reduziert!",
            'dues17_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    if (member.dues17_reduced and
            reduced_amount > member.dues17_amount_reduced or
            reduced_amount > member.dues17_amount):
        request.session.flash(
            u'Beitrag darf nicht über den berechneten oder bereits'
            u'reduzierten Wert gesetzt werden.',
            'dues17_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    # prepare: get highest invoice no from db
    max_invoice_no = Dues17Invoice.get_max_invoice_no()

    # things to be done:
    # * change dues amount for that member
    # * cancel old invoice by issuing a reversal invoice
    # * issue a new invoice with the new amount

    member.set_dues17_reduced_amount(reduced_amount)
    request.session.flash('reduction to {}'.format(reduced_amount),
                          'dues17_message_to_staff')

    old_invoice = Dues17Invoice.get_by_invoice_no(member.dues17_invoice_no)
    old_invoice.is_cancelled = True

    reversal_invoice_amount = -D(old_invoice.invoice_amount)

    # prepare reversal invoice number
    new_invoice_no = max_invoice_no + 1
    # create reversal invoice
    reversal_invoice = Dues17Invoice(
        invoice_no=new_invoice_no,
        invoice_no_string=(
            u'C3S-dues2017-' + str(new_invoice_no).zfill(4)) + '-S',
        invoice_date=datetime.today(),
        invoice_amount=reversal_invoice_amount.to_eng_string(),
        member_id=member.id,
        membership_no=member.membership_number,
        email=member.email,
        token=member.dues17_token,
    )
    reversal_invoice.preceding_invoice_no = old_invoice.invoice_no
    reversal_invoice.is_reversal = True
    DBSession.add(reversal_invoice)
    DBSession.flush()
    old_invoice.succeeding_invoice_no = new_invoice_no

    # check if this is an exemption (reduction to zero)
    is_exemption = False  # sane default
    # check if reduction to zero
    if reduced_amount.is_zero():
        is_exemption = True
        if DEBUG:
            print("this is an exemption: reduction to zero")
    else:
        if DEBUG:
            print("this is a reduction to {}".format(reduced_amount))

    if not is_exemption:
        # create new invoice
        new_invoice = Dues17Invoice(
            invoice_no=new_invoice_no + 1,
            invoice_no_string=(
                u'C3S-dues2017-' + str(new_invoice_no + 1).zfill(4)),
            invoice_date=datetime.today(),
            invoice_amount=u'' + str(reduced_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=member.dues17_token,
        )
        new_invoice.is_altered = True
        new_invoice.preceding_invoice_no = reversal_invoice.invoice_no
        reversal_invoice.succeeding_invoice_no = new_invoice_no + 1
        DBSession.add(new_invoice)

        # in the members record, store the current invoice no
        member.dues17_invoice_no = new_invoice_no + 1

        DBSession.flush()  # persist newer invoices

    reversal_url = (
        request.route_url(
            'make_dues17_reversal_invoice_pdf',
            email=member.email,
            code=member.dues17_token,
            no=str(reversal_invoice.invoice_no).zfill(4)
        )
    )
    if is_exemption:
        email_subject, email_body = make_dues_exemption_email(
            member,
            reversal_url)
    else:
        invoice_url = (
            request.route_url(
                'make_dues17_invoice_no_pdf',
                email=member.email,
                code=member.dues17_token,
                i=str(new_invoice_no + 1).zfill(4)
            )
        )
        email_subject, email_body = make_dues17_reduction_email(
            member,
            new_invoice,
            invoice_url,
            reversal_url)

    message = Message(
        subject=email_subject,
        sender=request.registry.settings[
            'c3smembership.notification_sender'],
        recipients=[member.email],
        body=email_body,
    )
    if is_exemption:
        request.session.flash('exemption email was sent to user!',
                              'dues17_message_to_staff')
    else:
        request.session.flash('update email was sent to user!',
                              'dues17_message_to_staff')
    send_message(request, message)
    return HTTPFound(
        request.route_url(
            'detail',
            memberid=member_id) +
        '#dues17')


@view_config(route_name='make_dues17_reversal_invoice_pdf')
def make_dues17_reversal_invoice_pdf(request):
    """
    This view checks supplied information (in URL) against info in database
    -- especially the invoice number --
    and conditionally returns
    - an error message or
    - a PDF
    """

    token = request.matchdict['code']
    invoice_number = request.matchdict['no']

    try:
        member = C3sMember.get_by_dues17_token(token)
        assert member is not None
        assert member.dues17_token == token

    except AssertionError:
        request.session.flash(
            u"This member and token did not match!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    try:
        invoice = Dues17Invoice.get_by_invoice_no(invoice_number)
        assert invoice is not None
    except AssertionError:
        request.session.flash(
            u"No invoice found!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # sanity check: invoice token must match with token
    try:
        assert(invoice.token == token)
    except AssertionError:
        request.session.flash(
            u"Token did not match!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # sanity check: reversal invoice token must be reversal
    try:
        assert(invoice.is_reversal)
    except AssertionError:
        request.session.flash(
            u"No reversal invoice found!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    # return a pdf file
    pdf_file = make_reversal_pdf_pdflatex(member, invoice)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)  # rewind to beginning
    response.app_iter = open(pdf_file.name, "r")
    return response


def make_reversal_pdf_pdflatex(member, invoice=None):
    """
    This function uses pdflatex to create a PDF
    as reversal invoice: cancel and balance out a former invoice.
    """

    dues17_archive_invoice = get_dues17_archive_invoice(invoice)
    if dues17_archive_invoice is not None:
        return dues17_archive_invoice

    pdflatex_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../../certificate/'
        ))
    # pdf backgrounds
    pdf_backgrounds = {
        'blank': pdflatex_dir + '/' + 'Urkunde_Hintergrund_blank.pdf',
    }

    # latex templates
    latex_templates = {
        'generic': pdflatex_dir + '/' + 'dues17_storno_de.tex',
        'generic_en': pdflatex_dir + '/' + 'dues17_storno_en.tex',
    }

    # choose background and template
    background = 'blank'
    template_name = 'generic' if 'de' in member.locale else 'generic_en'

    # pick background and template
    bg_pdf = pdf_backgrounds[background]
    tpl_tex = latex_templates[template_name]

    # pick temporary file for pdf
    receipt_pdf = tempfile.NamedTemporaryFile(prefix='storno_', suffix='.pdf')

    (path, filename) = os.path.split(receipt_pdf.name)
    filename = os.path.splitext(filename)[0]

    invoice_no = str(invoice.invoice_no).zfill(4) + '-S'
    invoice_date = invoice.invoice_date.strftime('%d. %m. %Y')
    # set variables for tex command
    tex_vars = {
        'personalFirstname': member.firstname,
        'personalLastname': member.lastname,
        'personalAddressOne': member.address1,
        'personalAddressTwo': member.address2,
        'personalPostCode': member.postcode,
        'personalCity': member.city,
        'personalMShipNo': unicode(member.membership_number),
        'invoiceNo': invoice_no,
        'invoiceDate': invoice_date,
        'duesAmount': unicode(invoice.invoice_amount),
        'origInvoiceRef': ('C3S-dues2017-' +
                           str(invoice.preceding_invoice_no).zfill(4)),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    # generate tex command for pdflatex
    tex_cmd = u''
    for key, val in iter(tex_vars.items()):
        tex_cmd += '\\newcommand{\\%s}{%s}' % (key, TexTools.escape(val))
    tex_cmd += '\\input{%s}' % tpl_tex
    tex_cmd = u'"'+tex_cmd+'"'

    # XXX: try to find out, why utf-8 doesn't work on debian
    subprocess.call(
        [
            'pdflatex',
            '-jobname', filename,
            '-output-directory', path,
            '-interaction', 'nonstopmode',
            '-halt-on-error',
            tex_cmd.encode('latin_1')
        ],
        stdout=open(os.devnull, 'w'),  # hide output
        stderr=subprocess.STDOUT,
        cwd=pdflatex_dir
    )

    # cleanup
    aux = os.path.join(path, filename + '.aux')
    if os.path.isfile(aux):
        os.unlink(aux)

    archive_dues17_invoice(receipt_pdf, invoice)

    return receipt_pdf


@view_config(
    route_name='dues17_notice',
    permission='manage')
def dues17_notice(request):
    """
    notice of arrival for transferral of dues
    """
    # member: sanity checks
    try:
        member_id = request.matchdict['member_id']
        member = C3sMember.get_by_id(member_id)  # is in database
        assert member.membership_accepted  # is a member
        assert 'investing' not in member.membership_type  # is normal member
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            u"No member OR not accepted OR not normal member",
            'dues17notice_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    # sanity check: the given amount is a positive decimal
    try:
        paid_amount = D(request.POST['amount'])
        assert not paid_amount.is_signed()
        if DEBUG:
            print("DEBUG: payment of {}".format(paid_amount))
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            (u"Invalid amount to pay: '{}' "
             u"Use the dot ('.') as decimal mark, e.g. '23.42'".format(
                 request.POST['amount'])),
            'dues17notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    # sanity check: the given date is a valid date
    try:
        paid_date = datetime.strptime(
            request.POST['payment_date'], '%Y-%m-%d')

        if DEBUG:
            print("DEBUG: payment received on {}".format(paid_date))
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            (u"Invalid date for payment: '{}' "
             u"Use YYYY-MM-DD, e.g. '2017-09-11'".format(
                 request.POST['payment_date'])),
            'dues17notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues17')

    # persist info about payment
    member.set_dues17_payment(paid_amount, paid_date)

    return HTTPFound(
        request.route_url('detail', memberid=member.id) + '#dues17')
