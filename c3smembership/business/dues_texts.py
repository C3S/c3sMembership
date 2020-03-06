# -*- coding: utf-8 -*-
"""
Email creation for invoices notifications.
"""
from c3smembership.mail_utils import (
    get_template_text,
    get_email_footer,
    get_salutation,
)


def make_dues15_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues15_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues16_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues16_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues17_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues17_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues18_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues18_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues19_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues19_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues20_invoice_email(member, invoice, invoice_url, invoice_quarter):
    """
    Create email subject and body for an invoice notification for full
    members.
    """
    return (get_template_text('dues_invoice_subject', member.locale),
            get_template_text('dues_invoice_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues20_amount),
                invoice_url=invoice_url,
                invoice_quarter=invoice_quarter,
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                footer=get_email_footer(member.locale)))


def make_dues15_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues15_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues16_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues16_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues17_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues17_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues18_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues18_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues19_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues19_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues20_reduction_email(member, invoice, invoice_url, reversal_url):
    """
    Create email subject and body for an invoice reduction.
    """
    return (get_template_text('dues_reduction_subject', member.locale),
            get_template_text('dues_reduction_body', member.locale).format(
                salutation=get_salutation(member),
                dues_amount=str(member.dues20_amount_reduced),
                invoice_number=invoice.invoice_no_string,
                membership_number=member.membership_number,
                invoice_url=invoice_url,
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues_exemption_email(member, reversal_url):
    """
    Create email subject and body for an invoice exemption.
    """
    return (get_template_text('dues_exemption_subject', member.locale),
            get_template_text('dues_exemption_body', member.locale).format(
                salutation=get_salutation(member),
                reversal_invoice_url=reversal_url,
                footer=get_email_footer(member.locale)))


def make_dues_invoice_investing_email(member):
    """
    Create email subject and body for an invoice notification for investing
    members.
    """
    return (get_template_text('dues_invoice_investing_subject', member.locale),
            get_template_text('dues_invoice_investing_body',
                              member.locale).format(
                                  salutation=get_salutation(member),
                                  membership_number=member.membership_number,
                                  footer=get_email_footer(member.locale)))


def make_dues_invoice_legalentity_email(member):
    """
    Create email subject and body for an invoice notification for legal entity
    members.
    """
    return (get_template_text('dues_invoice_legalentity_subject',
                              member.locale),
            get_template_text('dues_invoice_legalentity_body',
                              member.locale).format(
                                  salutation=get_salutation(member),
                                  legal_entity_name=member.lastname,
                                  membership_number=member.membership_number,
                                  footer=get_email_footer(member.locale)))
