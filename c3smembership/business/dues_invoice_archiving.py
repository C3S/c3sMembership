# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices.
"""

import os
import shutil


class IDuesInvoiceArchiving(object):
    """
    Offers functionality to archive invoices.
    """

    def __init__(self, db_session, c3s_member, dues_invoice_repository):
        """
        Initialises the MembershipApplication object.

        Args:
            db_session: Object implementing the query(class) method
                returning instances of the specified class.
            c3s_member: Class describing the c3s member.
            dues_invoice_repository: Object implementing the
                get_by_membership_number(membership_number, years) method
                returning invoice instances.
        """
        raise NotImplementedError()

    def generate_missing_invoice_pdfs(self, invoice_count):
        """
        Generates and archives a number of invoices which have not yet been
        archived.

        Args:
            invoice_count: The number of invoices to be generated and archived.

        Returns:
            An array of invoice numbers which were generated and archived.
        """
        raise NotImplementedError()


class DuesInvoiceArchiving(IDuesInvoiceArchiving):
    """
    Offers functionality to archive invoices.
    """

    def __init__(self, db_session, c3s_member, dues_invoice_repository,
                 make_invoice_pdf_pdflatex, make_reversal_pdf_pdflatex,
                 invoices_archive_path):
        """
        Initialises the MembershipApplication object.

        Args:
            db_session: Object implementing the query(class) method
                returning instances of the specified class.
            c3s_member: Class describing the c3s member.
            dues_invoice_repository: Object implementing the
                get_by_membership_number(membership_number, years) method
                returning invoice instances.
            make_invoice_pdf_pdflatex: Method taking member and invoice as
                arguments and returning the generated file.
            make_reversal_pdf_pdflatex: Method taking member and invoice as
                arguments and returning the generated file.
            invoices_archive_path: The absolute path in which the archived
                invoices are stored.
        """
        self._dbsession = db_session
        self._c3s_member = c3s_member
        self._dues_invoice_repository = dues_invoice_repository
        self._make_invoice_pdf_pdflatex = make_invoice_pdf_pdflatex
        self._make_reversal_pdf_pdflatex = make_reversal_pdf_pdflatex
        self._invoices_archive_path = invoices_archive_path
        if not os.path.isdir(self._invoices_archive_path):
            os.makedirs(self._invoices_archive_path)

    def generate_missing_invoice_pdfs(self, invoice_count):
        """
        Generates and archives a number of invoices which have not yet been
        archived.

        Args:
            invoice_count: The number of invoices to be generated and archived.

        Returns:
            An array of invoice numbers which were generated and archived.
        """
        members = self._dbsession.query(self._c3s_member)
        generated_files = []
        invoices_archive_path = self._invoices_archive_path
        counter = 0
        for member in members.all():
            invoices = self._dues_invoice_repository.get_by_membership_number(
                member.membership_number, [2015])
            for invoice in invoices:
                invoice_archive_filename = os.path.join(
                    invoices_archive_path,
                    '{0}.pdf'.format(invoice.invoice_no_string)
                )
                if not os.path.isfile(invoice_archive_filename):
                    pdf_file = self._generate_invoice_pdf(member, invoice)
                    generated_files.append(invoice.invoice_no_string)
                    shutil.copyfile(
                        pdf_file.name,
                        invoice_archive_filename
                    )
                    counter += 1
                    if counter >= invoice_count:
                        return generated_files
        return generated_files

    def _generate_invoice_pdf(self, member, invoice):
        pdf_file = None
        if invoice.is_reversal:
            pdf_file = self._make_reversal_pdf_pdflatex(member, invoice)
        else:
            pdf_file = self._make_invoice_pdf_pdflatex(member, invoice)
        return pdf_file
