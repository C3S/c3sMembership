# -*- coding: utf-8 -*-
"""
This module holds code for Membership Dues (2018 edition).

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
    timedelta,
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
from c3smembership.data.model.base.dues18invoice import Dues18Invoice

from c3smembership.mail_utils import send_message
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect
)
from c3smembership.presentation.views.dues_texts import (
    make_dues18_invoice_email,
    make_dues_invoice_investing_email,
    make_dues_invoice_legalentity_email,
    make_dues18_reduction_email,
    make_dues_exemption_email,
)
from c3smembership.tex_tools import TexTools


DEBUG = False
LOGGING = True

if LOGGING:  # pragma: no cover
    import logging
    LOG = logging.getLogger(__name__)

PDFLATEX_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../../../certificate/'
    ))

PDF_BACKGROUNDS = {
    'blank': PDFLATEX_DIR + '/' + 'Urkunde_Hintergrund_blank.pdf',
}

LATEX_TEMPLATES = {
    # 'generic': PDFLATEX_DIR + '/' + 'membership_dues_receipt.tex',
    'invoice_de': PDFLATEX_DIR + '/' + 'dues18_invoice_de.tex',
    'invoice_en': PDFLATEX_DIR + '/' + 'dues18_invoice_en.tex',
    'storno_de': PDFLATEX_DIR + '/' + 'dues18_storno_de.tex',
    'storno_en': PDFLATEX_DIR + '/' + 'dues18_storno_en.tex',
}


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


def calculate_partial_dues18(member):
    """
    helper function: calculate..

    * codified start quarter (q1, q2, q3, q4) and
    * dues

    depending on members entry date
    """
    if member.membership_date >= date(2019, 1, 1):
        raise ValueError('Member is not applicable for dues 2018.')

    if member.membership_date < date(2018, 4, 1):
        # first quarter of 2018 or earlier
        start = u'q1_2018'
        amount = D('50')
    elif member.membership_date < date(2018, 7, 1):
        # second quarter of 2018
        start = u'q2_2018'
        amount = D('37.50')
    elif member.membership_date < date(2018, 10, 1):
        # third quarter of 2018
        start = u'q3_2018'
        amount = D('25')
    elif member.membership_date >= date(2018, 10, 1):
        # third quarter of 2018
        start = u'q4_2018'
        amount = D('12.50')
    return (start, amount)


def string_start_quarter_dues18(member):
    """
    helper function: produce translated string for quarter of entry date
    depending on members locale
    """
    loc = member.locale
    result = u''
    if 'q1_2018' in member.dues18_start:  # first quarter of 2018 or earlier
        result = u"für das ganze Jahr" if 'de' in loc else "for the whole year"
    elif 'q2_2018' in member.dues18_start:  # second quarter of 2018
        result = u"ab Quartal 2" if 'de' in loc else u"from 2nd quarter"
    elif 'q3_2018' in member.dues18_start:  # third quarter of 2018
        result = u"ab Quartal 3" if 'de' in loc else u"from 3rd quarter"
    elif 'q4_2018' in member.dues18_start:  # third quarter of 2018
        result = u"ab Quartal 4" if 'de' in loc else u"from 4th quarter"
    return result


@view_config(
    permission='manage',
    route_name='send_dues18_invoice_email')
def send_dues18_invoice_email(request, m_id=None):
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
                'message_to_staff')
            return HTTPFound(request.route_url('toolbox'))

    # sanity check:is this a member?
    try:
        assert(member.membership_accepted)  # must be accepted member!
    except AssertionError:
        request.session.flash(
            "member {} not accepted by the board!".format(member_id),
            'message_to_staff')
        return HTTPFound(request.route_url('toolbox'))

    if 'normal' not in member.membership_type and \
            'investing' not in member.membership_type:
        request.session.flash(
            'The membership type of member {0} is not specified! The '
            'membership type must either be "normal" or "investing" in order '
            'to be able to send an invoice email.'.format(member.id),
            'message_to_staff')
        return get_memberhip_listing_redirect(request)
    if member.membership_date >= date(2019, 1, 1) or (
                member.membership_loss_date is not None
                and member.membership_loss_date < date(2018, 1, 1)
            ):
        request.session.flash(
            'Member {0} was not a member in 2018. Therefore, you cannot send '
            'an invoice for 2018.'.format(member.id),
            'message_to_staff')
        return get_memberhip_listing_redirect(request)

    # check if invoice no already exists.
    #     if yes: just send that email again!
    #     also: offer staffers to cancel this invoice

    if member.dues18_invoice is True:
        invoice = Dues18Invoice.get_by_invoice_no(member.dues18_invoice_no)
        member.dues18_invoice_date = datetime.now()

    else:  # if no invoice already exists:
        # make dues token and ...
        randomstring = make_random_string()
        # check if dues token is already used
        while (Dues18Invoice.check_for_existing_dues18_token(randomstring)):
            # create a new one, if the new one already exists in the database
            randomstring = make_random_string()  # pragma: no cover

        # prepare invoice number
        try:
            # either we already have an invoice number for that client...
            invoice_no = member.dues18_invoice_no
            assert invoice_no is not None
        except AssertionError:
            # ... or we create a new one and save it
            # get max invoice no from db
            max_invoice_no = Dues18Invoice.get_max_invoice_no()
            # use the next free number, save it to db
            new_invoice_no = int(max_invoice_no) + 1
            DBSession.flush()  # save dataset to DB

        # calculate dues amount (maybe partial, depending on quarter)
        dues_start, dues_amount = calculate_partial_dues18(member)

        # now we have enough info to update the member info
        # and persist invoice info for bookkeeping
        # store some info in DB/member table
        member.dues18_invoice = True
        member.dues18_invoice_no = new_invoice_no  # irrelevant for investing
        member.dues18_invoice_date = datetime.now()
        member.dues18_token = randomstring
        member.dues18_start = dues_start

        if 'normal' in member.membership_type:  # only for normal members
            member.set_dues18_amount(dues_amount)
            # store some more info about invoice in invoice table
            invoice = Dues18Invoice(
                invoice_no=member.dues18_invoice_no,
                invoice_no_string=(
                    u'C3S-dues2018-' + str(member.dues18_invoice_no).zfill(4)),
                invoice_date=member.dues18_invoice_date,
                invoice_amount=u'' + str(member.dues18_amount),
                member_id=member.id,
                membership_no=member.membership_number,
                email=member.email,
                token=member.dues18_token,
            )
            DBSession.add(invoice)
        DBSession.flush()

    # now: prepare that email
    # only normal (not investing) members *have to* pay the dues.
    # only the normal members get an invoice link and PDF produced for them.
    # only investing legalentities are asked for more support.
    if 'investing' not in member.membership_type:
        start_quarter = string_start_quarter_dues18(member)
        invoice_url = (
            request.route_url(
                'make_dues18_invoice_no_pdf',
                email=member.email,
                code=member.dues18_token,
                i=str(member.dues18_invoice_no).zfill(4)
            )
        )
        email_subject, email_body = make_dues18_invoice_email(
            member,
            invoice,
            invoice_url,
            start_quarter)
        message = Message(
            subject=email_subject,
            sender=request.registry.settings['c3smembership.mailaddr'],
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
            sender=request.registry.settings['c3smembership.mailaddr'],
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
            '#dues18')
    if 'toolbox' in request.referrer:
        return HTTPFound(request.route_url('toolbox'))
    else:
        return get_memberhip_listing_redirect(request, member.id)


@view_config(
    permission='manage',
    route_name='send_dues18_invoice_batch'
)
def send_dues18_invoice_batch(request):
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

    invoicees = C3sMember.get_dues18_invoicees(number)

    if len(invoicees) == 0:
        request.session.flash('no invoicees left. all done!',
                              'message_to_staff')
        return HTTPFound(request.route_url('toolbox'))

    emails_sent = 0
    ids_sent = []
    request.referrer = 'toolbox'

    for member in invoicees:
        send_dues18_invoice_email(request=request, m_id=member.id)
        emails_sent += 1
        ids_sent.append(member.id)

    request.session.flash(
        "sent out {} mails (to members with ids {})".format(
            emails_sent, ids_sent),
        'message_to_staff')

    return HTTPFound(request.route_url('toolbox'))


def get_dues18_invoice(invoice, request):
    """
    Gets the invoice and returns a PDF response.

    Args:
        invoice: The invoice for which the PDF is requested.
        request: The pyramid.request.Request object.

    Returns:
        A PDF response in case the invoice exists. Otherwise a redirect to the
        error page.
    """
    if invoice is None:
        request.session.flash(
            u'No invoice found!',
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    if invoice.is_reversal:
        pdf_file = make_reversal_pdf_pdflatex(invoice)
    else:
        pdf_file = make_invoice_pdf_pdflatex(invoice)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)
    response.app_iter = open(pdf_file.name, "r")
    return response


@view_config(
    route_name='dues18_invoice_pdf_backend',
    permission='manage')
def make_dues18_invoice_pdf_backend(request):
    """
    Show the invoice to a backend user
    """
    invoice_number = request.matchdict['i']
    invoice = Dues18Invoice.get_by_invoice_no(
        invoice_number.lstrip('0'))
    return get_dues18_invoice(invoice, request)


@view_config(route_name='make_dues18_invoice_no_pdf')
def make_dues18_invoice_no_pdf(request):
    """
    Show the invoice to a member verified by a URL token
    """
    token = request.matchdict['code']
    invoice_number = request.matchdict['i']
    invoice = Dues18Invoice.get_by_invoice_no(
        invoice_number.lstrip('0'))

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (
            date.today() - invoice.invoice_date.date() > timedelta(days=365))

    if invoice is None or token_is_invalid or invoice.is_reversal:
        request.session.flash(
            u"No invoice found!",
            'message_to_user'
        )
        return HTTPFound(request.route_url('error'))

    if older_than_a_year or member.dues18_paid:
        request.session.flash(
            u'This invoice cannot be downloaded anymore. '
            u'Please contact office@c3s.cc for further information.',
            'message_to_user'
        )
        return HTTPFound(request.route_url('error'))


    return get_dues18_invoice(invoice, request)


def get_dues18_invoice_archive_path():
    invoice_archive_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../../../invoices/'))
    if not os.path.isdir(invoice_archive_path):
        os.makedirs(invoice_archive_path)
    return invoice_archive_path


def get_dues18_archive_invoice_filename(invoice):
    return os.path.join(
        get_dues18_invoice_archive_path(),
        '{0}.pdf'.format(invoice.invoice_no_string))


def archive_dues18_invoice(pdf_file, invoice):
    invoice_archive_filename = get_dues18_archive_invoice_filename(
        invoice)
    if not os.path.isfile(invoice_archive_filename):
        shutil.copyfile(
            pdf_file.name,
            invoice_archive_filename
        )


def get_dues18_archive_invoice(invoice):
    invoice_archive_filename = get_dues18_archive_invoice_filename(
        invoice)
    if os.path.isfile(invoice_archive_filename):
        return open(invoice_archive_filename, 'rb')
    else:
        return None


def create_pdf(tex_vars, tpl_tex, invoice):
    receipt_pdf = tempfile.NamedTemporaryFile(suffix='.pdf')

    (path, filename) = os.path.split(receipt_pdf.name)
    filename = os.path.splitext(filename)[0]

    # generate tex command for pdflatex
    tex_cmd = u''
    for key, val in tex_vars.iteritems():
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
        cwd=PDFLATEX_DIR
    )

    # cleanup
    aux = os.path.join(path, filename + '.aux')
    if os.path.isfile(aux):
        os.unlink(aux)

    archive_dues18_invoice(receipt_pdf, invoice)

    return receipt_pdf


def make_invoice_pdf_pdflatex(invoice):
    """
    This function uses pdflatex to create a PDF
    as receipt for the members membership dues.

    default output is the current invoice.
    if i_no is suplied, the relevant invoice number is produced
    """

    dues18_archive_invoice = get_dues18_archive_invoice(invoice)
    if dues18_archive_invoice is not None:
        return dues18_archive_invoice

    member = C3sMember.get_by_id(invoice.member_id)

    template_name = 'invoice_de' if 'de' in member.locale else 'invoice_en'
    bg_pdf = PDF_BACKGROUNDS['blank']
    tpl_tex = LATEX_TEMPLATES[template_name]

    # on invoice, print start quarter or "reduced". prepare string:
    if (
            not invoice.is_reversal and
            invoice.is_altered and
            invoice.preceding_invoice_no is not None):
        is_altered_str = u'angepasst' if (
            'de' in member.locale) else u'altered'

    invoice_no = str(member.dues18_invoice_no).zfill(4)
    invoice_date = member.dues18_invoice_date.strftime('%d. %m. %Y')

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
        'account': unicode(-member.dues15_balance - member.dues16_balance
            - member.dues17_balance - member.dues18_balance),
        'duesStart':  is_altered_str if (
            invoice.is_altered) else string_start_quarter_dues18(member),
        'duesAmount': unicode(invoice.invoice_amount),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice)


@view_config(
    route_name='dues18_listing',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues18_list.pt'
)
def dues18_listing(request):
    """
    a listing of all invoices for the 2018 dues run.
    shall show both active/valid and cancelled/invalid invoices.
    """
    # get them all from the DB
    dues18_invoices = Dues18Invoice.get_all()

    return {
        'count': len(dues18_invoices),
        '_today': date.today(),
        'invoices': dues18_invoices,
    }


@view_config(
    route_name='dues18_reduction',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues18_list.pt'
)
def dues18_reduction(request):
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
            'dues18_message_to_staff'  # message queue for staff
        )
        return HTTPFound(

            request.route_url('detail', memberid=member.id) + '#dues18')

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
            'dues18_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    if DEBUG:
        print("DEBUG: member.dues18_amount: {}".format(
            member.dues18_amount))
        print("DEBUG: type(member.dues18_amount): {}".format(
            type(member.dues18_amount)))
        print("DEBUG: member.dues18_reduced: {}".format(
            member.dues18_reduced))
        print("DEBUG: member.dues18_amount_reduced: {}".format(
            member.dues18_amount_reduced))
        print("DEBUG: type(member.dues18_amount_reduced): {}".format(
            type(member.dues18_amount_reduced)))

    # The hidden input 'confirmed' must have the value 'yes' which is set by
    # the confirmation dialog.
    reduction_confirmed = request.POST['confirmed']
    if reduction_confirmed != 'yes':
        request.session.flash(
            u'Die Reduktion wurde nicht bestätigt.',
            'dues18_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    # check the reduction amount: same as default calculated amount?
    if (not member.dues18_reduced  and
            member.dues18_amount == reduced_amount):
        request.session.flash(
            u"Dieser Beitrag ist der default-Beitrag!",
            'dues18_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    if (member.dues18_reduced and
            reduced_amount == member.dues18_amount_reduced):
        request.session.flash(
            u"Auf diesen Beitrag wurde schon reduziert!",
            'dues18_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    if (member.dues18_reduced and
            reduced_amount > member.dues18_amount_reduced or
            reduced_amount > member.dues18_amount):
        request.session.flash(
            u'Beitrag darf nicht über den berechneten oder bereits'
            u'reduzierten Wert gesetzt werden.',
            'dues18_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    # prepare: get highest invoice no from db
    max_invoice_no = Dues18Invoice.get_max_invoice_no()

    # things to be done:
    # * change dues amount for that member
    # * cancel old invoice by issuing a reversal invoice
    # * issue a new invoice with the new amount

    member.set_dues18_reduced_amount(reduced_amount)
    request.session.flash('reduction to {}'.format(reduced_amount),
                          'dues18_message_to_staff')

    old_invoice = Dues18Invoice.get_by_invoice_no(member.dues18_invoice_no)
    old_invoice.is_cancelled = True

    reversal_invoice_amount = -D(old_invoice.invoice_amount)

    # prepare reversal invoice number
    new_invoice_no = max_invoice_no + 1
    # create reversal invoice
    reversal_invoice = Dues18Invoice(
        invoice_no=new_invoice_no,
        invoice_no_string=(
            u'C3S-dues2018-' + str(new_invoice_no).zfill(4)) + '-S',
        invoice_date=datetime.today(),
        invoice_amount=reversal_invoice_amount.to_eng_string(),
        member_id=member.id,
        membership_no=member.membership_number,
        email=member.email,
        token=member.dues18_token,
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
        new_invoice = Dues18Invoice(
            invoice_no=new_invoice_no + 1,
            invoice_no_string=(
                u'C3S-dues2018-' + str(new_invoice_no + 1).zfill(4)),
            invoice_date=datetime.today(),
            invoice_amount=u'' + str(reduced_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=member.dues18_token,
        )
        new_invoice.is_altered = True
        new_invoice.preceding_invoice_no = reversal_invoice.invoice_no
        reversal_invoice.succeeding_invoice_no = new_invoice_no + 1
        DBSession.add(new_invoice)

        # in the members record, store the current invoice no
        member.dues18_invoice_no = new_invoice_no + 1

        DBSession.flush()  # persist newer invoices

    reversal_url = (
        request.route_url(
            'make_dues18_reversal_invoice_pdf',
            email=member.email,
            code=member.dues18_token,
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
                'make_dues18_invoice_no_pdf',
                email=member.email,
                code=member.dues18_token,
                i=str(new_invoice_no + 1).zfill(4)
            )
        )
        email_subject, email_body = make_dues18_reduction_email(
            member,
            new_invoice,
            invoice_url,
            reversal_url)

    message = Message(
        subject=email_subject,
        sender=request.registry.settings['c3smembership.mailaddr'],
        recipients=[member.email],
        body=email_body,
    )
    if is_exemption:
        request.session.flash('exemption email was sent to user!',
                              'dues18_message_to_staff')
    else:
        request.session.flash('update email was sent to user!',
                              'dues18_message_to_staff')
    send_message(request, message)
    return HTTPFound(
        request.route_url(
            'detail',
            memberid=member_id) +
        '#dues18')


@view_config(
    route_name='dues18_reversal_pdf_backend',
    permission='manage')
def make_dues18_reversal_pdf_backend(request):
    """
    Show the invoice to a backend user
    """
    invoice_number = request.matchdict['i']
    invoice = Dues18Invoice.get_by_invoice_no(
        invoice_number.lstrip('0'))
    return get_dues18_invoice(invoice, request)


@view_config(route_name='make_dues18_reversal_invoice_pdf')
def make_dues18_reversal_invoice_pdf(request):
    """
    This view checks supplied information (in URL) against info in database
    -- especially the invoice number --
    and conditionally returns
    - an error message or
    - a PDF
    """

    token = request.matchdict['code']
    invoice_number = request.matchdict['no']
    invoice = Dues18Invoice.get_by_invoice_no(
        invoice_number.lstrip('0'))

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (
            date.today() - invoice.invoice_date.date() > timedelta(days=365))

    if invoice is None or token_is_invalid or not invoice.is_reversal \
            or older_than_a_year or member.dues18_paid:
        request.session.flash(
            u"No invoice found!",
            'message_to_user'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    pdf_file = make_reversal_pdf_pdflatex(invoice)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)  # rewind to beginning
    response.app_iter = open(pdf_file.name, "r")
    return response


def make_reversal_pdf_pdflatex(invoice):
    """
    This function uses pdflatex to create a PDF
    as reversal invoice: cancel and balance out a former invoice.
    """

    dues18_archive_invoice = get_dues18_archive_invoice(invoice)
    if dues18_archive_invoice is not None:
        return dues18_archive_invoice

    member = C3sMember.get_by_id(invoice.member_id)
    template_name = 'storno_de' if 'de' in member.locale else 'storno_en'
    bg_pdf = PDF_BACKGROUNDS['blank']
    tpl_tex = LATEX_TEMPLATES[template_name]
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
        'origInvoiceRef': ('C3S-dues2018-' +
                           str(invoice.preceding_invoice_no).zfill(4)),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice)


@view_config(
    route_name='dues18_notice',
    permission='manage')
def dues18_notice(request):
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
            'dues18notice_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

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
            'dues18notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    # sanity check: the given date is a valid date
    try:
        paid_date = datetime.strptime(
            request.POST['payment_date'], '%Y-%m-%d')

        if DEBUG:
            print("DEBUG: payment received on {}".format(paid_date))
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            (u"Invalid date for payment: '{}' "
             u"Use YYYY-MM-DD, e.g. '2018-09-11'".format(
                 request.POST['payment_date'])),
            'dues18notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', memberid=member.id) + '#dues18')

    # persist info about payment
    member.set_dues18_payment(paid_amount, paid_date)

    return HTTPFound(
        request.route_url('detail', memberid=member.id) + '#dues18')
