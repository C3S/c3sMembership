# -*- coding: utf-8 -*-
"""
Pyramid application configuration for membership dues.
"""

import os

from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.data.repository.payment_repository import \
    PaymentRepository

from c3smembership.business.dues_invoice_archiving import (
    DuesInvoiceArchiving
)
from c3smembership.business.payment_information import PaymentInformation

from c3smembership.presentation.configuration import Configuration
from c3smembership.presentation.views.dues_2015 import (
    make_invoice_pdf_pdflatex as make_invoice_2015,
    make_reversal_pdf_pdflatex as make_reversal_2015,
)
from c3smembership.presentation.views.dues_2016 import (
    make_invoice_pdf_pdflatex as make_invoice_2016,
    make_reversal_pdf_pdflatex as make_reversal_2016,
)
from c3smembership.presentation.views.dues_2017 import (
    make_invoice_pdf_pdflatex as make_invoice_2017,
    make_reversal_pdf_pdflatex as make_reversal_2017,
)
from c3smembership.presentation.views.dues_2018 import (
    make_invoice_pdf_pdflatex as make_invoice_2018,
    make_reversal_pdf_pdflatex as make_reversal_2018,
)
from c3smembership.presentation.views.dues_2019 import (
    make_invoice_pdf_pdflatex as make_invoice_2019,
    make_reversal_pdf_pdflatex as make_reversal_2019,
)
from c3smembership.presentation.views.dues_2019 import (
    make_invoice_pdf_pdflatex as make_invoice_2020,
    make_reversal_pdf_pdflatex as make_reversal_2020,
)
from c3smembership.presentation.views.payment_list import \
    payment_content_size_provider


class DuesConfig(Configuration):
    """
    Configuration for membership dues.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the membership dues business layer.
        """

        # Invoices
        invoices_archive_path = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '../../../invoices/'))
        self.config.registry.dues_invoice_archiving = DuesInvoiceArchiving(
            DuesInvoiceRepository,
            invoices_archive_path)
        self.config.registry.dues_invoice_archiving.configure_year(
            2015,
            make_invoice_2015,
            make_reversal_2015)
        self.config.registry.dues_invoice_archiving.configure_year(
            2016,
            make_invoice_2016,
            make_reversal_2016)
        self.config.registry.dues_invoice_archiving.configure_year(
            2017,
            make_invoice_2017,
            make_reversal_2017)
        self.config.registry.dues_invoice_archiving.configure_year(
            2018,
            make_invoice_2018,
            make_reversal_2018)
        self.config.registry.dues_invoice_archiving.configure_year(
            2019,
            make_invoice_2019,
            make_reversal_2019)
        self.config.registry.dues_invoice_archiving.configure_year(
            2020,
            make_invoice_2020,
            make_reversal_2020)

        # Payments
        self.config.registry.payment_information = PaymentInformation(
            PaymentRepository())
        self.config.make_pagination_route(
            'payment_list',
            payment_content_size_provider,
            sort_property_default='date',
            page_size_default=30)

    def configure_routes(self):
        """
        Configure the membership dues routes.
        """
        routes = [
            # Dues
            ('dues', '/dues'),

            # membership dues 2015
            (
                'dues15_invoice_pdf_backend',
                '/dues15_invoice/C3S-dues15-{invoice_number}.pdf'
            ),
            (
                'dues15_reversal_pdf_backend',
                '/dues15_reversal/C3S-dues15-{invoice_number}-S.pdf'
            ),
            ('send_dues15_invoice_email', '/dues15_invoice/{member_id}'),
            ('send_dues15_invoice_batch', '/dues15_invoice_batch'),
            (
                'make_dues15_invoice_no_pdf',
                '/dues15_invoice_no/{code}/C3S-dues15-{i}.pdf'
            ),
            # for backward compatibility
            (
                'make_dues15_invoice_no_pdf_email',
                '/dues15_invoice_no/{email}/{code}/C3S-dues15-{i}.pdf'
            ),
            ('dues15_reduction', '/dues15_reduction/{member_id}'),
            (
                'make_dues15_reversal_invoice_pdf',
                '/dues15_reversal/{code}/C3S-dues15-{no}-S.pdf'
            ),
            # for backward compatibility
            (
                'make_dues15_reversal_invoice_pdf_email',
                '/dues15_reversal/{email}/{code}/C3S-dues15-{no}-S.pdf'
            ),
            ('dues15_notice', '/dues15_notice/{member_id}'),
            ('dues15_listing', '/dues15_listing'),

            # membership dues 2016
            (
                'dues16_invoice_pdf_backend',
                '/dues16_invoice/C3S-dues16-{invoice_number}.pdf'
            ),
            (
                'dues16_reversal_pdf_backend',
                '/dues16_reversal/C3S-dues16-{invoice_number}-S.pdf'
            ),
            ('send_dues16_invoice_email', '/dues16_invoice/{member_id}'),
            ('send_dues16_invoice_batch', '/dues16_invoice_batch'),
            (
                'make_dues16_invoice_no_pdf',
                '/dues16_invoice_no/{code}/C3S-dues16-{i}.pdf'
            ),
            # for backward compatibility
            (
                'make_dues16_invoice_no_pdf_email',
                '/dues16_invoice_no/{email}/{code}/C3S-dues16-{i}.pdf'
            ),
            ('dues16_reduction', '/dues16_reduction/{member_id}'),
            (
                'make_dues16_reversal_invoice_pdf',
                '/dues16_reversal/{code}/C3S-dues16-{no}-S.pdf'
            ),
            # for backward compatibility
            (
                'make_dues16_reversal_invoice_pdf_email',
                '/dues16_reversal/{email}/{code}/C3S-dues16-{no}-S.pdf'
            ),
            ('dues16_notice', '/dues16_notice/{member_id}'),
            ('dues16_listing', '/dues16_listing'),

            # membership dues 2017
            (
                'dues17_invoice_pdf_backend',
                '/dues17_invoice/C3S-dues17-{invoice_number}.pdf'
            ),
            (
                'dues17_reversal_pdf_backend',
                '/dues17_reversal/C3S-dues17-{invoice_number}-S.pdf'
            ),
            ('send_dues17_invoice_email', '/dues17_invoice/{member_id}'),
            ('send_dues17_invoice_batch', '/dues17_invoice_batch'),
            (
                'make_dues17_invoice_no_pdf',
                '/dues17_invoice_no/{code}/C3S-dues17-{i}.pdf'
            ),
            ('dues17_reduction', '/dues17_reduction/{member_id}'),
            (
                'make_dues17_reversal_invoice_pdf',
                '/dues17_reversal/{code}/C3S-dues17-{no}-S.pdf'
            ),
            ('dues17_notice', '/dues17_notice/{member_id}'),
            ('dues17_listing', '/dues17_listing'),

            # membership dues 2018
            (
                'dues18_invoice_pdf_backend',
                '/dues18_invoice/C3S-dues18-{invoice_number}.pdf'
            ),
            (
                'dues18_reversal_pdf_backend',
                '/dues18_reversal/C3S-dues18-{invoice_number}-S.pdf'
            ),
            ('send_dues18_invoice_email', '/dues18_invoice/{member_id}'),
            ('send_dues18_invoice_batch', '/dues18_invoice_batch'),
            (
                'make_dues18_invoice_no_pdf',
                '/dues18_invoice_no/{code}/C3S-dues18-{i}.pdf'
            ),
            ('dues18_reduction', '/dues18_reduction/{member_id}'),

            (
                'make_dues18_reversal_invoice_pdf',
                '/dues18_reversal/{code}/C3S-dues18-{no}-S.pdf'
            ),
            ('dues18_notice', '/dues18_notice/{member_id}'),
            ('dues18_listing', '/dues18_listing'),

            # membership dues 2019
            (
                'dues19_invoice_pdf_backend',
                '/dues19_invoice/C3S-dues19-{invoice_number}.pdf'
            ),
            (
                'dues19_reversal_pdf_backend',
                '/dues19_reversal/C3S-dues19-{invoice_number}-S.pdf'
            ),
            ('send_dues19_invoice_email', '/dues19_invoice/{member_id}'),
            ('send_dues19_invoice_batch', '/dues19_invoice_batch'),
            (
                'make_dues19_invoice_no_pdf',
                '/dues19_invoice_no/{code}/C3S-dues19-{i}.pdf'
            ),
            ('dues19_reduction', '/dues19_reduction/{member_id}'),
            (
                'make_dues19_reversal_invoice_pdf',
                '/dues19_reversal/{code}/C3S-dues19-{no}-S.pdf'
            ),
            ('dues19_notice', '/dues19_notice/{member_id}'),
            ('dues19_listing', '/dues19_listing'),

            # membership dues 2020
            (
                'dues20_invoice_pdf_backend',
                '/dues20_invoice/C3S-dues20-{invoice_number}.pdf'
            ),
            (
                'dues20_reversal_pdf_backend',
                '/dues20_reversal/C3S-dues20-{invoice_number}-S.pdf'
            ),
            ('send_dues20_invoice_email', '/dues20_invoice/{member_id}'),
            ('send_dues20_invoice_batch', '/dues20_invoice_batch'),
            (
                'make_dues20_invoice_no_pdf',
                '/dues20_invoice_no/{code}/C3S-dues20-{i}.pdf'
            ),
            ('dues20_reduction', '/dues20_reduction/{member_id}'),
            (
                'make_dues20_reversal_invoice_pdf',
                '/dues20_reversal/{code}/C3S-dues20-{no}-S.pdf'
            ),
            ('dues20_notice', '/dues20_notice/{member_id}'),
            ('dues20_listing', '/dues20_listing'),

            # Archiving
            ('batch_archive_pdf_invoices', '/batch_archive_pdf_invoices'),
            (
                'background_archive_pdf_invoices',
                '/background_archive_pdf_invoices'
            ),

            # Payments
            ('payment_list', '/payments'),
        ]
        self._add_routes(routes)
