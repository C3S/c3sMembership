# -*- coding: utf-8 -*-
"""
Pyramid application configuration for membership dues.

Routes and views for all dues years are generated in a loop over
:data:`c3smembership.presentation.views.dues_year.DUES_YEARS`. Adding a new year
only requires bumping ``LATEST_DUES_YEAR`` in
:mod:`c3smembership.presentation.views.dues_year` and providing the LaTeX
templates -- no per-year code or data model change.
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
from c3smembership.presentation.schemas.member import MemberIdMatchdict
from c3smembership.presentation.view_processing.colander_validation import (
    ColanderMatchdictValidator)
from c3smembership.presentation.views import dues_year
from c3smembership.presentation.views.dues_year import DUES_YEARS
from c3smembership.presentation.views.payment_list import \
    payment_content_size_provider


DUES_LIST_RENDERER = (
    'c3smembership.presentation:templates/pages/dues_list.pt')

# The first dues years offered backward compatible invoice PDF routes which
# contained the member's email address in the URL.
EMAIL_ROUTE_YEARS = (2015, 2016)


def _year_view(view_func, year):
    """
    Bind a year-parametrized dues view function to a specific year.

    Returns a Pyramid view callable with the ``view(request)`` signature.
    """
    def view(request):
        return view_func(request, year)
    return view


class DuesConfig(Configuration):
    """
    Configuration for membership dues.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_views()
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
            invoices_archive_path,
            self.config.registry.settings['c3smembership.certificate_template']
        )
        # The PDF generators derive the year from the invoice itself, so the
        # same callables can be configured for every year.
        for year in DUES_YEARS:
            self.config.registry.dues_invoice_archiving.configure_year(
                year,
                dues_year.make_invoice_pdf_pdflatex,
                dues_year.make_reversal_pdf_pdflatex)

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
        ]

        for year in DUES_YEARS:
            short = year % 100
            routes.extend([
                (
                    'dues{0}_invoice_pdf_backend'.format(short),
                    '/dues{0}_invoice/C3S-dues{0}-{{invoice_number}}.pdf'
                    .format(short)
                ),
                (
                    'dues{0}_reversal_pdf_backend'.format(short),
                    '/dues{0}_reversal/C3S-dues{0}-{{invoice_number}}-S.pdf'
                    .format(short)
                ),
                (
                    'send_dues{0}_invoice_email'.format(short),
                    '/dues{0}_invoice/{{member_id}}'.format(short)
                ),
                (
                    'send_dues{0}_invoice_batch'.format(short),
                    '/dues{0}_invoice_batch'.format(short)
                ),
                (
                    'make_dues{0}_invoice_no_pdf'.format(short),
                    '/dues{0}_invoice_no/{{code}}/C3S-dues{0}-{{i}}.pdf'
                    .format(short)
                ),
                (
                    'dues{0}_reduction'.format(short),
                    '/dues{0}_reduction/{{member_id}}'.format(short)
                ),
                (
                    'make_dues{0}_reversal_invoice_pdf'.format(short),
                    '/dues{0}_reversal/{{code}}/C3S-dues{0}-{{no}}-S.pdf'
                    .format(short)
                ),
                (
                    'dues{0}_notice'.format(short),
                    '/dues{0}_notice/{{member_id}}'.format(short)
                ),
                (
                    'dues{0}_listing'.format(short),
                    '/dues{0}_listing'.format(short)
                ),
            ])
            if year in EMAIL_ROUTE_YEARS:
                # backward compatibility: URLs containing the email address
                routes.extend([
                    (
                        'make_dues{0}_invoice_no_pdf_email'.format(short),
                        '/dues{0}_invoice_no/{{email}}/{{code}}/'
                        'C3S-dues{0}-{{i}}.pdf'.format(short)
                    ),
                    (
                        'make_dues{0}_reversal_invoice_pdf_email'.format(short),
                        '/dues{0}_reversal/{{email}}/{{code}}/'
                        'C3S-dues{0}-{{no}}-S.pdf'.format(short)
                    ),
                ])

        # Archiving
        routes.extend([
            ('batch_archive_pdf_invoices', '/batch_archive_pdf_invoices'),
            (
                'background_archive_pdf_invoices',
                '/background_archive_pdf_invoices'
            ),
            # Payments
            ('payment_list', '/payments'),
        ])
        self._add_routes(routes)

    def configure_views(self):
        """
        Configure the membership dues views for all years.
        """
        config = self.config
        for year in DUES_YEARS:
            short = year % 100

            config.add_view(
                _year_view(dues_year.send_invoice_email, year),
                route_name='send_dues{0}_invoice_email'.format(short),
                permission='manage',
                pre_processor=ColanderMatchdictValidator(
                    MemberIdMatchdict(error_route='dues')))
            config.add_view(
                _year_view(dues_year.send_invoice_batch, year),
                route_name='send_dues{0}_invoice_batch'.format(short),
                permission='manage')
            config.add_view(
                _year_view(dues_year.make_invoice_pdf_backend, year),
                route_name='dues{0}_invoice_pdf_backend'.format(short),
                permission='manage')
            config.add_view(
                _year_view(dues_year.make_reversal_pdf_backend, year),
                route_name='dues{0}_reversal_pdf_backend'.format(short),
                permission='manage')
            config.add_view(
                _year_view(dues_year.make_invoice_no_pdf, year),
                route_name='make_dues{0}_invoice_no_pdf'.format(short))
            config.add_view(
                _year_view(dues_year.dues_reduction, year),
                route_name='dues{0}_reduction'.format(short),
                permission='manage',
                renderer=DUES_LIST_RENDERER)
            config.add_view(
                _year_view(dues_year.make_reversal_invoice_pdf, year),
                route_name='make_dues{0}_reversal_invoice_pdf'.format(short))
            config.add_view(
                _year_view(dues_year.dues_notice, year),
                route_name='dues{0}_notice'.format(short),
                permission='manage')
            config.add_view(
                _year_view(dues_year.dues_listing, year),
                route_name='dues{0}_listing'.format(short),
                permission='manage',
                renderer=DUES_LIST_RENDERER)

            if year in EMAIL_ROUTE_YEARS:
                config.add_view(
                    _year_view(dues_year.make_invoice_no_pdf, year),
                    route_name='make_dues{0}_invoice_no_pdf_email'
                    .format(short))
                config.add_view(
                    _year_view(dues_year.make_reversal_invoice_pdf, year),
                    route_name='make_dues{0}_reversal_invoice_pdf_email'
                    .format(short))
