# -*- coding: utf-8 -*-
"""
This module holds code for Membership Dues.

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
from decimal import (Decimal, InvalidOperation)
import logging
import os
import shutil
import subprocess
import tempfile

import babel.numbers

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from pyramid_mailer.message import Message

from c3smembership.business.dues import (
    calculate_dues_create_invoice,
    send_dues_invoice_email,
    DuesNotApplicableError,
    InvoiceUrlCreator,
    DuesEmailSender,
)
from c3smembership.business.dues_calculation import QuarterlyDuesCalculator
from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues21invoice import Dues21Invoice
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.mail_utils import send_message
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect)
from c3smembership.presentation.view_processing.colander_validation import (
    ColanderMatchdictValidator, )
from c3smembership.presentation.schemas.member import MemberIdMatchdict
from c3smembership.business.dues_texts import (
    make_dues_reduction_email,
    make_dues_exemption_email,
)
from c3smembership.tex_tools import TexTools

LOG = logging.getLogger(__name__)

PDFLATEX_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../../certificate/'))

PDF_BACKGROUNDS = {
    'blank': PDFLATEX_DIR + '/' + 'Urkunde_Hintergrund_blank.pdf',
}

LATEX_TEMPLATES = {
    'invoice_de': PDFLATEX_DIR + '/' + 'dues21_invoice_de.tex',
    'invoice_en': PDFLATEX_DIR + '/' + 'dues21_invoice_en.tex',
    'storno_de': PDFLATEX_DIR + '/' + 'dues21_storno_de.tex',
    'storno_en': PDFLATEX_DIR + '/' + 'dues21_storno_en.tex',
}

YEAR = 2021
DUES_CALCULATOR = QuarterlyDuesCalculator(Decimal('50'), YEAR)


def get_euro_string(euro_amount):
    """
    Get the Euro string of the Euro amount

    The Euro amount can be a Decimal or float. It will be formatted as a Euro
    string with decimal comma and thousand separator dot. The Euro string does
    not contain any Euro sign.
    """
    euro_string = babel.numbers.format_currency(euro_amount,
                                                'EUR',
                                                locale='de_DE')
    return euro_string.replace(u'\u20ac', '').replace(u'\xa0', '')


class PyramidInvoiceUrlCreator(InvoiceUrlCreator):
    """
    Create invoice URLs according the Pyramid routes
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, request):
        """
        Initialize the PyramidInvoiceUrlCreator object

        Args:
            request (pyramid.request.Request): The request used to create the
                route URLs.
        """
        self._request = request

    def __call__(self, year, member, invoice):
        """
        Create an invoice URL

        Args:
            year (int): The year of the invoice.
            member (C3sMember): The member of the invoice.
            invoice: The invoice for which the URL is created.

        Returns:
            A string representing the invoice URL.
        """
        invoice_year_route = ''
        invoice_code = ''
        invoice_number = ''

        if year == 2015:
            invoice_year_route = 'make_dues15_invoice_no_pdf'
            invoice_code = member.dues15_token
            invoice_number = member.dues15_invoice_no
        if year == 2016:
            invoice_year_route = 'make_dues16_invoice_no_pdf'
            invoice_code = member.dues16_token
            invoice_number = member.dues16_invoice_no
        if year == 2017:
            invoice_year_route = 'make_dues17_invoice_no_pdf'
            invoice_code = member.dues17_token
            invoice_number = member.dues17_invoice_no
        if year == 2018:
            invoice_year_route = 'make_dues18_invoice_no_pdf'
            invoice_code = member.dues18_token
            invoice_number = member.dues18_invoice_no
        if year == 2019:
            invoice_year_route = 'make_dues19_invoice_no_pdf'
            invoice_code = member.dues19_token
            invoice_number = member.dues19_invoice_no
        if year == 2020:
            invoice_year_route = 'make_dues20_invoice_no_pdf'
            invoice_code = member.dues21_token
            invoice_number = member.dues21_invoice_no
        if year == 2021:
            invoice_year_route = 'make_dues21_invoice_no_pdf'
            invoice_code = member.dues21_token
            invoice_number = member.dues21_invoice_no

        return self._request.route_url(invoice_year_route,
                                       email=member.email,
                                       code=invoice_code,
                                       i=str(invoice_number).zfill(4))


class PyramidDuesEmailSender(DuesEmailSender):
    """
    Send dues emails using pyramid_mailer
    """
    # pylint: disable=too-few-public-methods
    def __init__(self, request):
        """
        Initialize the PyramidDuesEmailSender object

        Args:
            request (pyramid.request.Request): The request used to send emails.
        """
        self._request = request

    def __call__(self, recipient, subject, body):
        """
        Send a dues email

        Args:
            recipient (str): The recipient of the dues email
            subject (str): The subject of the dues email
            body (str): The body of the dues email
        """
        message = Message(
            subject=subject,
            sender=self._request.registry.
            settings['c3smembership.notification_sender'],
            recipients=[recipient],
            body=body,
        )
        if 'true' in self._request.registry.settings[
                'testing.mail_to_console']:
            # pylint: disable=superfluous-parens
            print(message.body.encode('utf-8'))
        else:
            send_message(self._request, message)


@view_config(
    permission='manage',
    route_name='send_dues21_invoice_email',
    pre_processor=ColanderMatchdictValidator(
        MemberIdMatchdict(error_route='dues')),
)
def send_dues21_invoice_email(request, member_id=None):
    """
    Calculate dues, create invoice and send invoice emails

    Args:
        request: The Pyramid request containing a matchdict with set member_id.
        member_id: Optional. The member ID in case the view is called as a#
            method.

    Input validation: Member must exist. The matchdict member_id or member_id
    parameter must correspond to an existing member.
    """

    if member_id is not None:
        member = C3sMember.get_by_id(member_id)
        if member is None:
            raise ValueError('Member ID {} does not exist.'.format(member_id))
    else:
        member = request.validated_matchdict['member']

    try:
        invoice = calculate_dues_create_invoice(YEAR, member)
        send_dues_invoice_email(YEAR, member, invoice,
                                PyramidInvoiceUrlCreator(request),
                                PyramidDuesEmailSender(request))
    except DuesNotApplicableError as dues_not_applicable_error:
        request.session.flash(dues_not_applicable_error.message, 'warning')
        return get_memberhip_listing_redirect(request)

    return send_invoice_email_redirect(request, member)


def send_invoice_email_redirect(request, member):
    """
    Perform redirect after invoice email sending according to the referer.
    """
    if 'detail' in request.referer:
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')
    if 'dues' in request.referer:
        return HTTPFound(request.route_url('dues'))

    return get_memberhip_listing_redirect(request, member.id)


@view_config(permission='manage', route_name='send_dues21_invoice_batch')
def send_dues21_invoice_batch(request):
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

    invoicees = C3sMember.get_dues21_invoicees(number)

    if len(invoicees) == 0:
        request.session.flash('no invoicees left. all done!', 'success')
        return HTTPFound(request.route_url('dues'))

    emails_sent = 0
    membership_numbers_sent = []
    request.referrer = 'dues'

    for member in invoicees:
        send_dues21_invoice_email(request=request, member_id=member.id)
        emails_sent += 1
        membership_numbers_sent.append(member.membership_number)

    request.session.flash(
        "sent out {} mails (to members with membership numbers {})".format(
            emails_sent, membership_numbers_sent), 'success')

    return HTTPFound(request.route_url('dues'))


def get_dues21_invoice(invoice, request):
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
            'danger'  # message queue for user
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


@view_config(route_name='dues21_invoice_pdf_backend', permission='manage')
def make_dues21_invoice_pdf_backend(request):
    """
    Show the invoice to a backend user
    """
    invoice_number = request.matchdict['invoice_number']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  YEAR)
    return get_dues21_invoice(invoice, request)


@view_config(route_name='dues21_reversal_pdf_backend', permission='manage')
def make_dues21_reversal_pdf_backend(request):
    """
    Show the invoice to a backend user
    """
    invoice_number = request.matchdict['invoice_number']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  YEAR)
    return get_dues21_invoice(invoice, request)


@view_config(route_name='make_dues21_invoice_no_pdf')
def make_dues21_invoice_no_pdf(request):
    """
    Show the invoice to a member verified by a URL token
    """
    token = request.matchdict['code']
    invoice_number = request.matchdict['i']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  YEAR)

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (date.today() - invoice.invoice_date.date() >
                             timedelta(days=365))

    if invoice is None or token_is_invalid or invoice.is_reversal:
        request.session.flash(u"No invoice found!", 'warning')
        return HTTPFound(request.route_url('error'))

    if older_than_a_year or member.dues21_paid:
        request.session.flash(
            u'This invoice cannot be downloaded anymore. '
            u'Please contact office@c3s.cc for further information.',
            'warning')
        return HTTPFound(request.route_url('error'))

    return get_dues21_invoice(invoice, request)


def get_dues21_invoice_archive_path():
    """
    Get the invoice archive path
    """
    invoice_archive_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '../../../invoices/'))
    if not os.path.isdir(invoice_archive_path):
        os.makedirs(invoice_archive_path)
    return invoice_archive_path


def get_dues21_archive_invoice_filename(invoice):
    """
    Get the archive filename of the invoice
    """
    return os.path.join(get_dues21_invoice_archive_path(),
                        '{0}.pdf'.format(invoice.invoice_no_string))


def archive_dues21_invoice(pdf_file, invoice):
    """
    Archive the invoice if it is not yet archived
    """
    invoice_archive_filename = get_dues21_archive_invoice_filename(invoice)
    if not os.path.isfile(invoice_archive_filename):
        shutil.copyfile(pdf_file.name, invoice_archive_filename)


def get_dues21_archive_invoice(invoice):
    """
    Get the invoice from the archive
    """
    invoice_archive_filename = get_dues21_archive_invoice_filename(invoice)
    if os.path.isfile(invoice_archive_filename):
        return open(invoice_archive_filename, 'rb')

    return None


def create_pdf(tex_vars, tpl_tex, invoice):
    """
    Create the invoice PDF
    """
    receipt_pdf = tempfile.NamedTemporaryFile(suffix='.pdf')

    (path, filename) = os.path.split(receipt_pdf.name)
    filename = os.path.splitext(filename)[0]

    # generate tex command for pdflatex
    tex_cmd = u''
    for key, val in tex_vars.iteritems():
        tex_cmd += '\\newcommand{\\%s}{%s}' % (key, TexTools.escape(val))
    tex_cmd += '\\input{%s}' % tpl_tex
    tex_cmd = u'"' + tex_cmd + '"'

    # make latex show ß correctly in pdf:
    tex_cmd = tex_cmd.replace(u'ß', u'\\ss{}')

    subprocess.call(
        [
            'pdflatex', '-jobname', filename, '-output-directory', path,
            '-interaction', 'nonstopmode', '-halt-on-error',
            tex_cmd.encode('latin_1')
        ],
        stdout=open(os.devnull, 'w'),  # hide output
        stderr=subprocess.STDOUT,
        cwd=PDFLATEX_DIR)

    # cleanup
    aux = os.path.join(path, filename + '.aux')
    if os.path.isfile(aux):
        os.unlink(aux)

    # TODO: If the compilation fails, the invoice is still copied to archive.
    # In this case it is most likely empty and afterwards cannot be regenerated
    # as it already exists. The fix has to implement proper error handling. If
    # the generation fails the invoice must not be archived.
    archive_dues21_invoice(receipt_pdf, invoice)

    return receipt_pdf


def make_invoice_pdf_pdflatex(invoice):
    """
    This function uses pdflatex to create a PDF
    as receipt for the members membership dues.

    default output is the current invoice.
    if i_no is suplied, the relevant invoice number is produced
    """

    dues21_archive_invoice = get_dues21_archive_invoice(invoice)
    if dues21_archive_invoice is not None:
        return dues21_archive_invoice

    member = C3sMember.get_by_id(invoice.member_id)

    template_name = 'invoice_de' if 'de' in member.locale else 'invoice_en'
    bg_pdf = PDF_BACKGROUNDS['blank']
    tpl_tex = LATEX_TEMPLATES[template_name]

    # on invoice, print start quarter or "reduced". prepare string:
    if (not invoice.is_reversal and invoice.is_altered
            and invoice.preceding_invoice_no is not None):
        is_altered_str = u'angepasst' if (
            'de' in member.locale) else u'altered'

    invoice_no = str(invoice.invoice_no).zfill(4)
    invoice_date = invoice.invoice_date.strftime('%d. %m. %Y')

    # set variables for tex command
    dues_start = DUES_CALCULATOR.get_description(
        DUES_CALCULATOR.calculate_quarter(member), member.locale)

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
        'account':
            get_euro_string(-member.dues15_balance - member.dues16_balance -
                            member.dues17_balance - member.dues18_balance -
                            member.dues19_balance - member.dues21_balance),
        'duesStart': is_altered_str if (invoice.is_altered) else dues_start,
        'duesAmount': get_euro_string(invoice.invoice_amount),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice)


@view_config(
    route_name='dues21_listing',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues21_list.pt')
def dues21_listing(request):
    """
    a listing of all invoices.
    shall show both active/valid and cancelled/invalid invoices.
    """
    # pylint: disable=unused-argument
    dues21_invoices = DuesInvoiceRepository.get_all([YEAR])
    return {
        'count': len(dues21_invoices),
        '_today': date.today(),
        'invoices': dues21_invoices,
    }


@view_config(
    route_name='dues21_reduction',
    permission='manage',
    renderer='c3smembership.presentation:templates/pages/dues21_list.pt')
def dues21_reduction(request):
    """
    reduce a members dues upon valid request to do so.

    * change payable amount for member
    * cancel old invoice by issuing a cancellation
    * issue a new invoice with the new amount (if new amount != 0)

    this will only work for *normal* members.
    """
    member_id = request.matchdict.get('member_id')
    member = C3sMember.get_by_id(member_id)  # is in database
    if (member is None or not member.membership_accepted
            or not member.dues21_invoice):
        request.session.flash(
            u"Member not found or not a member or no invoice to reduce",
            'dues21notice_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # sanity check: the given amount is a positive decimal
    try:
        reduced_amount = Decimal(request.POST['amount'])
        assert not reduced_amount.is_signed()
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            (u"Invalid amount to reduce to: '{}' "
             u"Use the dot ('.') as decimal mark, e.g. '23.42'".format(
                 request.POST['amount'])),
            'dues21_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # The hidden input 'confirmed' must have the value 'yes' which is set by
    # the confirmation dialog.
    reduction_confirmed = request.POST['confirmed']
    if reduction_confirmed != 'yes':
        request.session.flash(
            u'Die Reduktion wurde nicht bestätigt.',
            'dues21_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # check the reduction amount: same as default calculated amount?
    if (not member.dues21_reduced and member.dues21_amount == reduced_amount):
        request.session.flash(
            u"Dieser Beitrag ist der default-Beitrag!",
            'dues21_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    if (member.dues21_reduced
            and reduced_amount == member.dues21_amount_reduced):
        request.session.flash(
            u"Auf diesen Beitrag wurde schon reduziert!",
            'dues21_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    if (member.dues21_reduced and reduced_amount > member.dues21_amount_reduced
            or reduced_amount > member.dues21_amount):
        request.session.flash(
            u'Beitrag darf nicht über den berechneten oder bereits'
            u'reduzierten Wert gesetzt werden.',
            'dues21_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # prepare: get highest invoice no from db
    max_invoice_no = DuesInvoiceRepository.get_max_invoice_number(YEAR)

    # things to be done:
    # * change dues amount for that member
    # * cancel old invoice by issuing a reversal invoice
    # * issue a new invoice with the new amount

    member.set_dues21_reduced_amount(reduced_amount)
    request.session.flash('reduction to {}'.format(reduced_amount),
                          'dues21_message_to_staff')

    old_invoice = DuesInvoiceRepository.get_by_number(member.dues21_invoice_no,
                                                      YEAR)
    old_invoice.is_cancelled = True

    reversal_invoice_amount = -Decimal(old_invoice.invoice_amount)

    # prepare reversal invoice number
    new_invoice_no = max_invoice_no + 1
    # create reversal invoice
    reversal_invoice = Dues21Invoice(
        invoice_no=new_invoice_no,
        invoice_no_string=(u'C3S-dues{0}-{1}-S'.format(
            YEAR,
            str(new_invoice_no).zfill(4))),
        invoice_date=datetime.today(),
        invoice_amount=reversal_invoice_amount.to_eng_string(),
        member_id=member.id,
        membership_no=member.membership_number,
        email=member.email,
        token=member.dues21_token,
    )
    reversal_invoice.preceding_invoice_no = old_invoice.invoice_no
    reversal_invoice.is_reversal = True
    DBSession().add(reversal_invoice)
    DBSession().flush()
    old_invoice.succeeding_invoice_no = new_invoice_no

    # check if this is an exemption (reduction to zero)
    is_exemption = False  # sane default
    # check if reduction to zero
    if reduced_amount.is_zero():
        is_exemption = True

    if not is_exemption:
        # create new invoice
        new_invoice = Dues21Invoice(
            invoice_no=new_invoice_no + 1,
            invoice_no_string=(u'C3S-dues{0}-{1}'.format(
                YEAR,
                str(new_invoice_no + 1).zfill(4))),
            invoice_date=datetime.today(),
            invoice_amount=u'' + str(reduced_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=member.dues21_token,
        )
        new_invoice.is_altered = True
        new_invoice.preceding_invoice_no = reversal_invoice.invoice_no
        reversal_invoice.succeeding_invoice_no = new_invoice_no + 1
        DBSession().add(new_invoice)

        # in the members record, store the current invoice no
        member.dues21_invoice_no = new_invoice_no + 1

        DBSession().flush()  # persist newer invoices

    reversal_url = (request.route_url(
        'make_dues21_reversal_invoice_pdf',
        email=member.email,
        code=member.dues21_token,
        no=str(reversal_invoice.invoice_no).zfill(4)))
    if is_exemption:
        email_subject, email_body = make_dues_exemption_email(
            member, reversal_url)
    else:
        invoice_url = (request.route_url('make_dues21_invoice_no_pdf',
                                         email=member.email,
                                         code=member.dues21_token,
                                         i=str(new_invoice_no + 1).zfill(4)))
        email_subject, email_body = make_dues_reduction_email(
            member, new_invoice, invoice_url, reversal_url)

    message = Message(
        subject=email_subject,
        sender=request.registry.settings['c3smembership.notification_sender'],
        recipients=[member.email],
        body=email_body,
    )
    if is_exemption:
        request.session.flash('exemption email was sent to user!',
                              'dues21_message_to_staff')
    else:
        request.session.flash('update email was sent to user!',
                              'dues21_message_to_staff')
    send_message(request, message)
    return HTTPFound(
        request.route_url('detail', member_id=member_id) + '#dues21')


@view_config(route_name='make_dues21_reversal_invoice_pdf')
def make_dues21_reversal_invoice_pdf(request):
    """
    This view checks supplied information (in URL) against info in database
    -- especially the invoice number --
    and conditionally returns
    - an error message or
    - a PDF
    """
    token = request.matchdict['code']
    invoice_number = request.matchdict['no']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  YEAR)

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (date.today() - invoice.invoice_date.date() >
                             timedelta(days=365))

    if invoice is None or token_is_invalid or not invoice.is_reversal:
        request.session.flash(u"No invoice found!", 'warning')
        return HTTPFound(request.route_url('error'))

    if older_than_a_year or member.dues21_paid:
        request.session.flash(
            u'This invoice cannot be downloaded anymore. '
            u'Please contact office@c3s.cc for further information.',
            'warning')
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

    dues21_archive_invoice = get_dues21_archive_invoice(invoice)
    if dues21_archive_invoice is not None:
        return dues21_archive_invoice

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
        'duesAmount': get_euro_string(invoice.invoice_amount),
        'origInvoiceRef': ('C3S-dues{0}-{1}'.format(
            YEAR,
            str(invoice.preceding_invoice_no).zfill(4))),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice)


@view_config(route_name='dues21_notice', permission='manage')
def dues21_notice(request):
    """
    notice of arrival for transferral of dues
    """
    member_id = request.matchdict.get('member_id')
    member = C3sMember.get_by_id(member_id)  # is in database
    if (member is None or not member.membership_accepted
            or not member.dues21_invoice):
        request.session.flash(
            u"Member not found or not a member or no invoice to pay for",
            'dues21notice_message_to_staff'  # message queue for staff
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # sanity check: the given amount is a positive decimal
    try:
        paid_amount = Decimal(request.POST['amount'])
        assert not paid_amount.is_signed()
    except (KeyError, AssertionError, InvalidOperation):  # pragma: no cover
        request.session.flash(
            (u"Invalid amount to pay: '{}' "
             u"Use the dot ('.') as decimal mark, e.g. '23.42'".format(
                 request.POST['amount'])),
            'dues21notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # sanity check: the given date is a valid date
    try:
        paid_date = datetime.strptime(request.POST['payment_date'], '%Y-%m-%d')
    except (KeyError, ValueError):  # pragma: no cover
        request.session.flash(
            (u"Invalid date for payment: '{}' "
             u"Use YYYY-MM-DD, e.g. '1999-09-11'".format(
                 request.POST['payment_date'])),
            'dues21notice_message_to_staff'  # message queue for user
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id) + '#dues21')

    # persist info about payment
    member.set_dues21_payment(paid_amount, paid_date)

    return HTTPFound(
        request.route_url('detail', member_id=member.id) + '#dues21')
