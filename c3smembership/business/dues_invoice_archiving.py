# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices.
"""

import os
import shutil


class DuesInvoiceArchiving(object):
    """
    Offers functionality to archive invoices.
    """

    def __init__(self, dues_invoice_repository, invoices_archive_path):
        """
        Initialises the MembershipApplication object.

        Args:
            dues_invoice_repository: Object implementing the
                get_by_membership_number(membership_number, years) method
                returning invoice instances.
            invoices_archive_path: The absolute path in which the archived
                invoices are stored.
        """
        self._dues_invoice_repository = dues_invoice_repository
        self._invoices_archive_path = invoices_archive_path
        self._generate_pdf = {}
        if not os.path.isdir(self._invoices_archive_path):
            os.makedirs(self._invoices_archive_path)

    def configure_year(
            self, year, generate_invoice, generate_reversal):
        """
        Configure the PDF generation for a specific year

        Args:
            year: The numeric four digit year, e.g. 2015
            generate_invoice: The Python callable generating the invoice PDF
            generate_reversal: The Python callable generating the reversal PDF
        """
        self._generate_pdf[year] = {}
        self._generate_pdf[year]['invoice'] = generate_invoice
        self._generate_pdf[year]['reversal'] = generate_reversal

    def get_configured_years(self):
        """
        Get the years for which archiving is configured
        """
        return sorted(self._generate_pdf.keys())

    def generate_missing_invoice_pdfs(self, year, invoice_count):
        """
        Generates and archives a number of invoices which have not yet been
        archived.

        Args:
            year: The year for which missing invoices are generated.
            invoice_count: The number of invoices to be generated and archived.

        Returns:
            An array of invoice numbers which were generated and archived.
        """
        missing_invoices = self.get_missing_invoices(year)
        generated_files = []
        for invoice in missing_invoices[:invoice_count]:
            pdf_file = self._generate_invoice_pdf(invoice, year)
            shutil.copyfile(
                pdf_file.name,
                self._get_archive_filename(invoice)
            )
            generated_files.append(invoice.invoice_no_string)
        return generated_files

    def _generate_invoice_pdf(self, invoice, year):
        """
        Generate the PDF depending on the type

        Types are invoice and reversal.
        """
        pdf_file = None
        if invoice.is_reversal:
            pdf_file = self._generate_pdf[year]['reversal'](invoice)
        else:
            pdf_file = self._generate_pdf[year]['invoice'](invoice)
        return pdf_file

    def get_missing_invoices(self, year):
        """
        Get the missing invoices for a given year
        """
        missing_invoices = []
        invoices = self._dues_invoice_repository.get_all([year])
        for invoice in invoices:
            if not self._is_invoice_archived(invoice):
                missing_invoices.append(invoice)
        return missing_invoices

    def get_archiving_stats(self):
        """
        Get statistics about the archiving for all years
        """
        archiving_stats = []
        years = self.get_configured_years()
        for year in years:
            total = len(self._dues_invoice_repository.get_all([year]))
            not_archived = len(self.get_missing_invoices(year))
            archiving_stats.append({
                'year': year,
                'total': total,
                'archived': total - not_archived,
                'not_archived': not_archived})
        return archiving_stats

    def _is_invoice_archived(self, invoice):
        """
        Indicate whether the invoice is archived
        """
        return os.path.isfile(self._get_archive_filename(invoice))

    def _get_archive_filename(self, invoice):
        """
        Get the full archive filename of the invoice
        """
        return os.path.join(
            self._invoices_archive_path,
            '{0}.pdf'.format(invoice.invoice_no_string)
        )
