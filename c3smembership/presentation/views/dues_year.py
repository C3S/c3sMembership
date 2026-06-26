# -*- coding: utf-8 -*-
"""
Year-agnostic membership dues views.

This single module replaces the former per-year ``dues_2015`` ... ``dues_2026``
view modules. Every view callable is parametrized by ``year`` and registered for
each configured year in
:mod:`c3smembership.presentation.configuration.dues_config`.

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
from pyramid_mailer.message import Message

from c3smembership.business.dues import (
    calculate_dues_create_invoice,
    send_dues_invoice_email,
    DuesNotApplicableError,
    InvoiceUrlCreator,
    DuesEmailSender,
)
from c3smembership.business.dues_calculation import QuarterlyDuesCalculator
from c3smembership.business.dues_texts import (
    make_dues_reduction_email,
    make_dues_exemption_email,
)
from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues_invoice import DuesInvoice
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.mail_utils import send_message
from c3smembership.presentation.views.dues_years import (  # noqa: F401
    DUES_YEARS,
    LATEST_DUES_YEAR,
)
from c3smembership.presentation.views.membership_listing import (
    get_memberhip_listing_redirect)
from c3smembership.tex_tools import TexTools

LOG = logging.getLogger(__name__)

PDFLATEX_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '../../../certificate/'))

PDF_BACKGROUNDS = {
    'blank': PDFLATEX_DIR + '/{}/' + 'Urkunde_Hintergrund_blank.pdf',
}

# Most years use the regular ``duesNN_<kind>.tex`` naming. The first dues year
# (2015) uses versioned file names which are mapped here.
LATEX_TEMPLATE_OVERRIDES = {
    2015: {
        'invoice_de': 'dues15_invoice_de_v0.2.tex',
        'invoice_en': 'dues15_invoice_en_v0.2.tex',
        'storno_de': 'dues15_storno_de_v0.1.tex',
        'storno_en': 'dues15_storno_en_v0.1.tex',
    },
}


def latex_template(year, kind):
    """
    Get the absolute LaTeX template path pattern for the year and kind.

    Args:
        year (int): The dues year, e.g. 2026.
        kind (str): One of ``invoice_de``, ``invoice_en``, ``storno_de``,
            ``storno_en``.

    Returns:
        A path pattern still containing the ``{}`` placeholder for the
        certificate template directory.
    """
    overrides = LATEX_TEMPLATE_OVERRIDES.get(year, {})
    filename = overrides.get(kind, 'dues{0}_{1}.tex'.format(year % 100, kind))
    return PDFLATEX_DIR + '/{}/' + filename


def dues_calculator(year):
    """
    Get the quarterly dues calculator for the year.
    """
    return QuarterlyDuesCalculator(Decimal('50'), year)


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
    return euro_string.replace('€', '').replace('\xa0', '')


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
        dues = member.get_dues(year)
        return self._request.route_url(
            'make_dues{0}_invoice_no_pdf'.format(year % 100),
            email=member.email,
            code=dues.token,
            i=str(dues.invoice_no).zfill(4))


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
            print((message.body.encode('utf-8')))
        else:
            send_message(self._request, message)


def send_invoice_email(request, year, member_id=None):
    """
    Calculate dues, create invoice and send invoice emails

    Args:
        request: The Pyramid request containing a matchdict with set member_id.
        year: The dues year.
        member_id: Optional. The member ID in case the view is called as a
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
        invoice = calculate_dues_create_invoice(year, member)
        send_dues_invoice_email(year, member, invoice,
                                PyramidInvoiceUrlCreator(request),
                                PyramidDuesEmailSender(request))
    except DuesNotApplicableError as dues_not_applicable_error:
        request.session.flash(str(dues_not_applicable_error), 'warning')
        return get_memberhip_listing_redirect(request)

    return send_invoice_email_redirect(request, year, member)


def send_invoice_email_redirect(request, year, member):
    """
    Perform redirect after invoice email sending according to the referer.
    """
    if 'detail' in request.referer:
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(year % 100))
    if 'dues' in request.referer:
        return HTTPFound(request.route_url('dues'))

    return get_memberhip_listing_redirect(request, member.id)


def send_invoice_batch(request, year):
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

    invoicees = C3sMember.get_dues_invoicees(year, number)

    if len(invoicees) == 0:
        request.session.flash('no invoicees left. all done!', 'success')
        return HTTPFound(request.route_url('dues'))

    emails_sent = 0
    membership_numbers_sent = []
    request.referrer = 'dues'

    for member in invoicees:
        send_invoice_email(request=request, year=year, member_id=member.id)
        emails_sent += 1
        membership_numbers_sent.append(member.membership_number)

    request.session.flash(
        "sent out {} mails (to members with membership numbers {})".format(
            emails_sent, membership_numbers_sent), 'success')

    return HTTPFound(request.route_url('dues'))


def get_invoice_response(invoice, request):
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
            'No invoice found!',
            'danger'  # message queue for user
        )
        return HTTPFound(request.route_url('error'))

    template = request.registry.settings['c3smembership.certificate_template']
    if invoice.is_reversal:
        pdf_file = make_reversal_pdf_pdflatex(invoice, template)
    else:
        pdf_file = make_invoice_pdf_pdflatex(invoice, template)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)
    response.app_iter = open(pdf_file.name, "rb")
    return response


def make_invoice_pdf_backend(request, year):
    """
    Show the invoice to a backend user
    """
    invoice_number = request.matchdict['invoice_number']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  year)
    return get_invoice_response(invoice, request)


def make_reversal_pdf_backend(request, year):
    """
    Show the reversal invoice to a backend user
    """
    invoice_number = request.matchdict['invoice_number']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  year)
    return get_invoice_response(invoice, request)


def make_invoice_no_pdf(request, year):
    """
    Show the invoice to a member verified by a URL token
    """
    token = request.matchdict['code']
    invoice_number = request.matchdict['i']
    invoice = DuesInvoiceRepository.get_by_number(invoice_number.lstrip('0'),
                                                  year)

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (date.today() - invoice.invoice_date.date() >
                             timedelta(days=365))

    if invoice is None or token_is_invalid or invoice.is_reversal:
        request.session.flash("No invoice found!", 'warning')
        return HTTPFound(request.route_url('error'))

    if older_than_a_year or member.get_dues(year).paid:
        request.session.flash(
            'This invoice cannot be downloaded anymore. '
            'Please contact office@c3s.cc for further information.',
            'warning')
        return HTTPFound(request.route_url('error'))

    return get_invoice_response(invoice, request)


def get_invoice_archive_path():
    """
    Get the invoice archive path
    """
    invoice_archive_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '../../../invoices/'))
    if not os.path.isdir(invoice_archive_path):
        os.makedirs(invoice_archive_path)
    return invoice_archive_path


def get_archive_invoice_filename(invoice):
    """
    Get the archive filename of the invoice
    """
    return os.path.join(get_invoice_archive_path(),
                        '{0}.pdf'.format(invoice.invoice_no_string))


def archive_invoice(pdf_file, invoice):
    """
    Archive the invoice if it is not yet archived
    """
    invoice_archive_filename = get_archive_invoice_filename(invoice)
    if not os.path.isfile(invoice_archive_filename):
        shutil.copyfile(pdf_file.name, invoice_archive_filename)


def get_archive_invoice(invoice):
    """
    Get the invoice from the archive
    """
    invoice_archive_filename = get_archive_invoice_filename(invoice)
    if os.path.isfile(invoice_archive_filename):
        return open(invoice_archive_filename, 'rb')

    return None


def create_pdf(tex_vars, tpl_tex, invoice, template):
    """
    Create the invoice PDF
    """
    receipt_pdf = tempfile.NamedTemporaryFile(suffix='.pdf')

    (path, filename) = os.path.split(receipt_pdf.name)
    filename = os.path.splitext(filename)[0]

    # generate tex command for pdflatex
    tex_cmd = ''
    for key, val in tex_vars.items():
        tex_cmd += '\\newcommand{\\%s}{%s}' % (key, TexTools.escape(val))
    tex_cmd += '\\input{%s}' % tpl_tex
    tex_cmd = '"' + tex_cmd + '"'

    # make latex show ß correctly in pdf:
    tex_cmd = tex_cmd.replace('ß', '\\ss{}')

    cmd = [
        'pdflatex', '-jobname', filename, '-output-directory', path,
        '-interaction', 'nonstopmode', '-halt-on-error',
        tex_cmd.encode('utf-8')
    ]

    subprocess.call(
        cmd,
        stdout=open(os.devnull, 'w'),  # hide output
        stderr=subprocess.STDOUT,
        cwd=os.path.join(PDFLATEX_DIR, template)
    )

    # cleanup
    aux = os.path.join(path, filename + '.aux')
    if os.path.isfile(aux):
        os.unlink(aux)

    # archive
    if os.fstat(receipt_pdf.fileno()).st_size:
        archive_invoice(receipt_pdf, invoice)

    return receipt_pdf


def make_invoice_pdf_pdflatex(invoice, template):
    """
    This function uses pdflatex to create a PDF
    as receipt for the members membership dues.

    The dues year is taken from the invoice.
    """
    archived_invoice = get_archive_invoice(invoice)
    if archived_invoice is not None:
        return archived_invoice

    year = invoice.year
    member = C3sMember.get_by_id(invoice.member_id)
    calculator = dues_calculator(year)

    template_name = 'invoice_de' if 'de' in member.locale else 'invoice_en'
    bg_pdf = PDF_BACKGROUNDS['blank'].format(template)
    tpl_tex = latex_template(year, template_name).format(template)

    # on invoice, print start quarter or "reduced". prepare string:
    is_altered_str = ''
    if (not invoice.is_reversal and invoice.is_altered
            and invoice.preceding_invoice_no is not None):
        is_altered_str = 'angepasst' if (
            'de' in member.locale) else 'altered'

    invoice_no = str(invoice.invoice_no).zfill(4)
    invoice_date = invoice.invoice_date.strftime('%d. %m. %Y')

    # set variables for tex command
    dues_start = calculator.get_description(
        calculator.calculate_quarter(member), member.locale)

    # the account balance is the sum of all the member's dues balances
    account_balance = -sum(
        (dues.balance for dues in member.dues), Decimal('0'))

    tex_vars = {
        'personalFirstname': member.firstname,
        'personalLastname': member.lastname,
        'personalAddressOne': member.address1,
        'personalAddressTwo': member.address2,
        'personalPostCode': member.postcode,
        'personalCity': member.city,
        'personalMShipNo': str(member.membership_number),
        'invoiceNo': invoice_no,
        'invoiceDate': invoice_date,
        'account': get_euro_string(account_balance),
        'duesStart': is_altered_str if (invoice.is_altered) else dues_start,
        'duesAmount': get_euro_string(invoice.invoice_amount),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice, template)


def make_reversal_pdf_pdflatex(invoice, template):
    """
    This function uses pdflatex to create a PDF
    as reversal invoice: cancel and balance out a former invoice.

    The dues year is taken from the invoice.
    """
    archived_invoice = get_archive_invoice(invoice)
    if archived_invoice is not None:
        return archived_invoice

    year = invoice.year
    member = C3sMember.get_by_id(invoice.member_id)
    template_name = 'storno_de' if 'de' in member.locale else 'storno_en'
    bg_pdf = PDF_BACKGROUNDS['blank'].format(template)
    tpl_tex = latex_template(year, template_name).format(template)
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
        'personalMShipNo': str(member.membership_number),
        'invoiceNo': invoice_no,
        'invoiceDate': invoice_date,
        'duesAmount': get_euro_string(invoice.invoice_amount),
        'origInvoiceRef': ('C3S-dues{0}-{1}'.format(
            year,
            str(invoice.preceding_invoice_no).zfill(4))),
        'lang': 'de',
        'pdfBackground': bg_pdf,
    }

    return create_pdf(tex_vars, tpl_tex, invoice, template)


def dues_listing(request, year):
    """
    A listing of all invoices for the dues year.

    Shows both active/valid and cancelled/invalid invoices.
    """
    invoices = DuesInvoiceRepository.get_all([year])
    return {
        'year': year,
        'count': len(invoices),
        '_today': date.today(),
        'invoices': invoices,
    }


def dues_reduction(request, year):
    """
    reduce a members dues upon valid request to do so.

    * change payable amount for member
    * cancel old invoice by issuing a cancellation
    * issue a new invoice with the new amount (if new amount != 0)

    this will only work for *normal* members.
    """
    short = year % 100
    member_id = request.matchdict.get('member_id')
    member = C3sMember.get_by_id(member_id)  # is in database
    dues = member.get_dues(year) if member is not None else None
    if (member is None or not member.membership_accepted
            or not dues.invoice):
        request.session.flash(
            "Member not found or not a member or no invoice to reduce",
            'dues{0}notice_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # sanity check: the given amount is a positive decimal
    try:
        reduced_amount = Decimal(request.POST['amount'])
        assert not reduced_amount.is_signed()
    except (KeyError, AssertionError):  # pragma: no cover
        request.session.flash(
            ("Invalid amount to reduce to: '{}' "
             "Use the dot ('.') as decimal mark, e.g. '26.42'".format(
                 request.POST['amount'])),
            'dues{0}_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # The hidden input 'confirmed' must have the value 'yes' which is set by
    # the confirmation dialog.
    reduction_confirmed = request.POST['confirmed']
    if reduction_confirmed != 'yes':
        request.session.flash(
            'Die Reduktion wurde nicht bestätigt.',
            'dues{0}_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # check the reduction amount: same as default calculated amount?
    if (not dues.reduced and dues.amount == reduced_amount):
        request.session.flash(
            "Dieser Beitrag ist der default-Beitrag!",
            'dues{0}_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    if (dues.reduced and reduced_amount == dues.amount_reduced):
        request.session.flash(
            "Auf diesen Beitrag wurde schon reduziert!",
            'dues{0}_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    if (dues.reduced and reduced_amount > dues.amount_reduced
            or reduced_amount > dues.amount):
        request.session.flash(
            'Beitrag darf nicht über den berechneten oder bereits'
            'reduzierten Wert gesetzt werden.',
            'dues{0}_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # prepare: get highest invoice no from db
    max_invoice_no = DuesInvoiceRepository.get_max_invoice_number(year)

    # things to be done:
    # * change dues amount for that member
    # * cancel old invoice by issuing a reversal invoice
    # * issue a new invoice with the new amount

    dues.set_reduced_amount(reduced_amount)
    request.session.flash('reduction to {}'.format(reduced_amount),
                          'dues{0}_message_to_staff'.format(short))

    old_invoice = DuesInvoiceRepository.get_by_number(dues.invoice_no, year)
    old_invoice.is_cancelled = True

    reversal_invoice_amount = -Decimal(old_invoice.invoice_amount)

    # prepare reversal invoice number
    new_invoice_no = max_invoice_no + 1
    # create reversal invoice
    reversal_invoice = DuesInvoice(
        year=year,
        invoice_no=new_invoice_no,
        invoice_no_string=('C3S-dues{0}-{1}-S'.format(
            year,
            str(new_invoice_no).zfill(4))),
        invoice_date=datetime.today(),
        invoice_amount=reversal_invoice_amount.to_eng_string(),
        member_id=member.id,
        membership_no=member.membership_number,
        email=member.email,
        token=dues.token,
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
        new_invoice = DuesInvoice(
            year=year,
            invoice_no=new_invoice_no + 1,
            invoice_no_string=('C3S-dues{0}-{1}'.format(
                year,
                str(new_invoice_no + 1).zfill(4))),
            invoice_date=datetime.today(),
            invoice_amount='' + str(reduced_amount),
            member_id=member.id,
            membership_no=member.membership_number,
            email=member.email,
            token=dues.token,
        )
        new_invoice.is_altered = True
        new_invoice.preceding_invoice_no = reversal_invoice.invoice_no
        reversal_invoice.succeeding_invoice_no = new_invoice_no + 1
        DBSession().add(new_invoice)

        # in the member's dues account, store the current invoice no
        dues.invoice_no = new_invoice_no + 1

        DBSession().flush()  # persist newer invoices

    reversal_url = (request.route_url(
        'make_dues{0}_reversal_invoice_pdf'.format(short),
        email=member.email,
        code=dues.token,
        no=str(reversal_invoice.invoice_no).zfill(4)))
    if is_exemption:
        email_subject, email_body = make_dues_exemption_email(
            member, reversal_url)
    else:
        invoice_url = (request.route_url(
            'make_dues{0}_invoice_no_pdf'.format(short),
            email=member.email,
            code=dues.token,
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
                              'dues{0}_message_to_staff'.format(short))
    else:
        request.session.flash('update email was sent to user!',
                              'dues{0}_message_to_staff'.format(short))
    send_message(request, message)
    return HTTPFound(
        request.route_url('detail', member_id=member_id)
        + '#dues{0}'.format(short))


def make_reversal_invoice_pdf(request, year):
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
                                                  year)

    member = None
    token_is_invalid = True
    older_than_a_year = True
    if invoice is not None:
        member = C3sMember.get_by_id(invoice.member_id)
        token_is_invalid = token != invoice.token
        older_than_a_year = (date.today() - invoice.invoice_date.date() >
                             timedelta(days=365))

    if invoice is None or token_is_invalid or not invoice.is_reversal:
        request.session.flash("No invoice found!", 'warning')
        return HTTPFound(request.route_url('error'))

    if older_than_a_year or member.get_dues(year).paid:
        request.session.flash(
            'This invoice cannot be downloaded anymore. '
            'Please contact office@c3s.cc for further information.',
            'warning')
        return HTTPFound(request.route_url('error'))

    template = request.registry.settings['c3smembership.certificate_template']
    pdf_file = make_reversal_pdf_pdflatex(invoice, template)
    response = Response(content_type='application/pdf')
    pdf_file.seek(0)  # rewind to beginning
    response.app_iter = open(pdf_file.name, "rb")
    return response


def dues_notice(request, year):
    """
    notice of arrival for transferral of dues
    """
    short = year % 100
    member_id = request.matchdict.get('member_id')
    member = C3sMember.get_by_id(member_id)  # is in database
    dues = member.get_dues(year) if member is not None else None
    if (member is None or not member.membership_accepted
            or not dues.invoice):
        request.session.flash(
            "Member not found or not a member or no invoice to pay for",
            'dues{0}notice_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # sanity check: the given amount is a positive decimal
    try:
        paid_amount = Decimal(request.POST['amount'])
        assert not paid_amount.is_signed()
    except (KeyError, AssertionError, InvalidOperation):  # pragma: no cover
        request.session.flash(
            ("Invalid amount to pay: '{}' "
             "Use the dot ('.') as decimal mark, e.g. '26.42'".format(
                 request.POST['amount'])),
            'dues{0}notice_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # sanity check: the given date is a valid date
    try:
        paid_date = datetime.strptime(request.POST['payment_date'], '%Y-%m-%d')
    except (KeyError, ValueError):  # pragma: no cover
        request.session.flash(
            ("Invalid date for payment: '{}' "
             "Use YYYY-MM-DD, e.g. '1999-09-11'".format(
                 request.POST['payment_date'])),
            'dues{0}notice_message_to_staff'.format(short)
        )
        return HTTPFound(
            request.route_url('detail', member_id=member.id)
            + '#dues{0}'.format(short))

    # persist info about payment
    dues.set_payment(paid_amount, paid_date)

    return HTTPFound(
        request.route_url('detail', member_id=member.id)
        + '#dues{0}'.format(short))
