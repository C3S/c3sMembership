# -*- coding: utf-8 -*-
"""
Handle membership dues
"""
# TODO: The business layer must use a data layer repository for data
# manipulation instead of using the database session and records directly.

from datetime import (date, datetime)
from decimal import Decimal
import random
import string

from c3smembership.data.model.base import DBSession
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository

from c3smembership.business.dues_calculation import QuarterlyDuesCalculator
from c3smembership.business.dues_texts import (
    make_dues_invoice_email,
    make_dues_invoice_investing_email,
    make_dues_invoice_legalentity_email,
)


class DuesNotApplicableError(ValueError):
    """
    Dues are not applicable to the member
    """
    pass


def calculate_dues_create_invoice(year, member):
    """
    Calculate the dues and create an invoice record

    The invoice PDF is not created. If the dues were created before, the
    existing invoice record will be returned.

    Business validation:

    - 1 Membership within the dues year

      - 1.1 Membership started before the end of the dues year
      - 1.2 Membership ended after the beginning of the dues year

    - 2 User must be logged in as staff

    Business logic:

    - 1 Due calculation for normal members

      - 1.1 Calculate quarterly dues
      - 1.2 Store dues data
      - 1.3 Store invoice data
      - 1.4 Generate invoice PDF (not implemented here yet)

    - 2 No dues calculation for investing members
    - 3 Send email depending on membership type and entity type

      - 3.1 Normal members get email with invoice link
      - 3.2 Investing members get email

        - 3.2.1 For legal entities with request for amount based on turnover
        - 3.2.2 For natural persons with request for normal amount

      - 3.3 Send email in German if member language is German
      - 3.4 Send email in English for other member languages than German
      - 3.5 Email is sent to member's email address

    - 4 Store that and when dues were calculated and email was sent
    - 5 If called again only resend email but only calculate dues once
    """
    # TODO: Implement PDF invoice generation

    _validate_member_dues_applicable(year, member)

    invoice = None
    # Get invoice if it exists already
    if _invoice_calculated(year, member):
        invoice = DuesInvoiceRepository.get_by_number(
            _get_year_invoice_number(year, member), year)
    else:
        # Otherweise calculate dues and invoice for normal members
        if 'normal' in member.membership_type:
            dues_calculator = _get_dues_calculator(year)
            dues_calculation = dues_calculator.calculate(member)
            invoice = create_dues_invoice(year, member,
                                          dues_calculation.amount)
            DuesInvoiceRepository.store_dues(year, member, dues_calculation)
            DBSession().flush()
    return invoice


def is_dues_applicable(year, member):
    """
    Indicates whether the dues for the year are applicable to the member

    Args:
        year (int): The year of the membership dues.
        member (C3sMember): The member for which the check is performed.

    Returns:
        (indicator, reason): Tuple of indicator (bool) and reason (unicode).
        Indicator indicates whether the does for the year are applicable to the
        member. In case the dues are not applicable a reason is specified.
    """
    if not member.membership_accepted:
        return (False,
                'Member {} not accepted by the board!'.format(member.id))

    if member.membership_date >= date(year + 1, 1, 1) or (
            member.membership_loss_date is not None
            and member.membership_loss_date < date(year, 1, 1)):
        return (
            False,
            'Member {0} was not a member in {1}. Therefore, the member is not '
            'applicable for dues in {1}.'.format(member.id, year))

    return True, u''


def create_dues_invoice(year, member, dues_amount):
    """
    Create the invoice record

    The invoice PDF is not created.

    Args:
        year (int): The year for which the dues invoice is created.
        member (C3sMember): The member for which the dues invoice is created.
        invoice_amount (Decimal): The amount for which the invoice is created.

    Business logic:

    - Create new invoice number by getting last per year and incrementing
    - Create invoice number string like C3S-dues2020-1234 for invoice number
      1234 in year 2020
    - Generate unique invoice token to identify the invoice
    """
    max_invoice_no = DuesInvoiceRepository.get_max_invoice_number(year)
    new_invoice_no = int(max_invoice_no) + 1

    invoice = DuesInvoiceRepository.create_dues_invoice(
        year,
        member,
        invoice_number=new_invoice_no,
        invoice_number_string=(u'C3S-dues{0}-{1}'.format(
            year,
            str(new_invoice_no).zfill(4))),
        invoice_amount=dues_amount,
        invoice_token=_make_random_string())

    return invoice


def send_dues_invoice_email(year, member, invoice, invoice_url_creator,
                            dues_email_sender):
    """
    Send the dues email depending on the membership type

    Normal members get an email with the invoice URL. Investing members get a
    recommendation of how much dues to pay.
    """
    if 'normal' in member.membership_type:
        email_subject, email_body = _create_dues_email_normal(
            year, member, invoice, invoice_url_creator)
    elif 'investing' in member.membership_type:
        email_subject, email_body = _create_dues_email_investing(member)

    dues_email_sender(member.email, email_subject, email_body)
    _record_dues_email_sent(year, member)


def _validate_member_dues_applicable(year, member):
    """
    Validate that the member is applicable for the dues of the year

    Args:
        year (int): The year for which the dues applicability is validated.
        member (C3sMember): The member for which the dues applicability is
            valildate.

    Raises:
        DuesNotApplicableError in case the member is not applicable for the
        dues of the year.
    """
    (indicator, reason) = is_dues_applicable(year, member)
    if not indicator:
        raise DuesNotApplicableError(reason)


def _make_random_string():
    """
    Generate a random string used as a dues token
    """
    return u''.join(random.choice(string.ascii_uppercase) for x in range(10))


def _get_dues_calculator(year):
    """
    Get the dues calculator for the year

    The dues calculator bases on 50 € dues per year and calculates a quarterly
    amount.
    """
    return QuarterlyDuesCalculator(Decimal('50'), year)


def _create_dues_email_normal(year, member, invoice, invoice_url_creator):
    """
    Create the dues email for normal members
    """
    dues_calculator = _get_dues_calculator(year)
    dues_description = dues_calculator.get_description(
        dues_calculator.calculate_quarter(member), member.locale)
    start_quarter = dues_description
    invoice_url = invoice_url_creator(year, member, invoice)
    email_subject, email_body = make_dues_invoice_email(
        member, invoice, invoice_url, start_quarter)
    return (email_subject, email_body)


def _create_dues_email_investing(member):
    """
    Create the dues email for investing members
    """
    if member.is_legalentity:
        email_subject, email_body = \
            make_dues_invoice_legalentity_email(member)
    else:
        email_subject, email_body = \
            make_dues_invoice_investing_email(member)
    return email_subject, email_body


class InvoiceUrlCreator(object):
    """
    Create invoice URLs according to the presentation layer

    The presentation layer knows how to create invoice URLs as it handles
    these. With an implementation of the InvoiceUrlCreator the presentation
    layer hands down the ability to create such an URL which can then be
    included into emails.
    """
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
        raise NotImplementedError()


class DuesEmailSender(object):
    """
    Send dues emails

    The presentation layer knows how to send emails. With an implementation of
    the DuesEmailSender the presentation layer hands down the ability to send
    dues emails to the business layer.
    """
    def __call__(self, recipient, subject, body):
        """
        Send a dues email

        Args:
            recipient (str): The recipient of the dues email
            subject (str): The subject of the dues email
            body (str): The body of the dues email
        """
        raise NotImplementedError()


def _get_year_invoice_number(year, member):
    """
    Get the year's invoice number
    """
    # TODO: This is only a workaround until the data model has been cleaned up
    # and there is an extra table to record dues per year and member.
    year_invoice_number = {
        2015: member.dues15_invoice_no,
        2016: member.dues16_invoice_no,
        2017: member.dues17_invoice_no,
        2018: member.dues18_invoice_no,
        2019: member.dues19_invoice_no,
        2020: member.dues20_invoice_no,
    }
    return year_invoice_number[year]


def _invoice_calculated(year, member):
    """
    Check whether the invoice for the year was calculated
    """
    # TODO: This is only a workaround until the data model has been cleaned up
    # and there is an extra table to record dues per year and member.
    year_invoice_calculated = {
        2015: member.dues15_invoice,
        2016: member.dues16_invoice,
        2017: member.dues17_invoice,
        2018: member.dues18_invoice,
        2019: member.dues19_invoice,
        2020: member.dues20_invoice,
    }
    return year_invoice_calculated[year]


def _record_dues_email_sent(year, member):
    """
    Record the fact that the dues email was sent and when it was sent
    """
    # TODO: This is only a workaround until the data model has been cleaned up
    # and there is an extra table to record dues per year and member.
    invoice_date = datetime.now()
    if year == 2015:
        member.dues15_invoice = True
        member.dues15_invoice_date = invoice_date
    if year == 2016:
        member.dues16_invoice = True
        member.dues16_invoice_date = invoice_date
    if year == 2017:
        member.dues17_invoice = True
        member.dues17_invoice_date = invoice_date
    if year == 2018:
        member.dues18_invoice = True
        member.dues18_invoice_date = invoice_date
    if year == 2019:
        member.dues19_invoice = True
        member.dues19_invoice_date = invoice_date
    if year == 2020:
        member.dues20_invoice = True
        member.dues20_invoice_date = invoice_date
