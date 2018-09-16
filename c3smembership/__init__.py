# -*- coding: utf-8 -*-
"""
This module holds the main method: config and route declarations
"""

import os

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from sqlalchemy import engine_from_config

from c3smembership.data.model.base import Base
from c3smembership.security.request import RequestWithUserAttribute
from c3smembership.security import (
    Root,
    groupfinder
)
from c3smembership.presentation.views.membership_acquisition import (
    dashboard_content_size_provider
)
from c3smembership.presentation.views.membership_listing import (
    membership_content_size_provider
)

# Import for SqlAlchemy metadata detection. Currently, the metadata detection
# only covers some of the tables probably because they are imported here.
# Others are not covered maybe because they are not directly imported but only
# through view discovery. There might be a better and cleaner solution to this
# problem but hasn't been discovered yet.
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice


__version__ = open(os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '../VERSION')).read()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    session_factory = session_factory_from_settings(settings)

    authn_policy = AuthTktAuthenticationPolicy(
        's0secret!!',
        callback=groupfinder,)
    authz_policy = ACLAuthorizationPolicy()

    Base.metadata.bind = engine

    config = Configurator(settings=settings,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          session_factory=session_factory,
                          root_factory=Root)

    # using a custom request with user information
    config.set_request_factory(RequestWithUserAttribute)

    includes = [
        'pyramid_mailer',
        'pyramid_chameleon',
        'cornice',
        'c3smembership.presentation.pagination',
    ]

    for include in includes:
        config.include(include)

    config.add_translation_dirs(
        'colander:locale/',
        'deform:locale/',
        'c3smembership:locale/')

    config.add_static_view('static_deform', 'deform:static')
    config.add_static_view(
        'static',
        'c3smembership:static',
        cache_max_age=3600)
    config.add_static_view(
        'docs',
        '../docs/_build/html/',
        cache_max_age=3600)

    subscribers = [
        (
            'c3smembership.subscribers.add_frontend_template',
            'pyramid.events.BeforeRender',
        ),
        (
            'c3smembership.subscribers.add_backend_template',
            'pyramid.events.BeforeRender',
        ),
        (
            'c3smembership.subscribers.add_old_backend_template',
            'pyramid.events.BeforeRender',
        ),
        (
            'c3smembership.subscribers.add_locale_to_cookie',
            'pyramid.events.NewRequest',
        ),
    ]
    for subscriber in subscribers:
        config.add_subscriber(subscriber[0], subscriber[1])

    config.add_renderer(name='csv',
                        factory='c3smembership.renderers.CSVRenderer')

    from c3smembership.data.repository.share_repository import ShareRepository
    from c3smembership.business.share_acquisition import ShareAcquisition
    share_acquisition = ShareAcquisition(ShareRepository)
    config.registry.share_acquisition = share_acquisition

    from pyramid_mailer import get_mailer
    config.registry.get_mailer = get_mailer

    routes = [
        # Membership application process
        # Step 1 (join.pt): home is /, the membership application form
        ('join', '/'),
        # Step 2 (success.pt): check and edit data
        ('success', '/success'),
        # Step 3 email was sent (check-mail.pt): send verification email
        # address
        ('success_check_email', '/check_email'),
        # Still step 3 (verify_password.pt): enter password
        # and step 4 (verify_password.pt): download form
        ('verify_email_password', '/verify/{email}/{code}'),  # PDF
        # PDF download of Step 4.
        ('success_pdf', '/C3S_SCE_AFM_{namepart}.pdf'),  # download

        # applications for membership
        ('dashboard', '/dashboard'),

        ('toolbox', '/membership-tools'),
        ('stats', '/stats'),
        ('staff', '/staff'),
        ('new_member', '/new_member'),
        ('detail', '/detail/{memberid}'),
        ('member_details', '/members/{membership_number}'),
        ('edit', '/edit/{_id}'),

        ('switch_sig', '/switch_sig/{memberid}'),
        ('switch_pay', '/switch_pay/{memberid}'),

        ('mail_sig_confirmation', '/mail_sig_conf/{memberid}'),
        ('regenerate_pdf', '/re_C3S_SCE_AFM_{code}.pdf'),
        ('mail_pay_confirmation', '/mail_pay_conf/{member_id}'),
        ('mail_mail_confirmation', '/mail_mail_conf/{member_id}'),
        ('mail_sig_reminder', '/mail_sig_reminder/{memberid}'),
        ('mail_pay_reminder', '/mail_pay_reminder/{memberid}'),
        ('delete_entry', '/delete/{memberid}'),
        ('delete_afms', '/delete_afms'),
        ('login', '/login'),
        ('logout', '/logout'),

        # applications for membership
        ('afms_awaiting_approval', '/afms_awaiting_approval'),

        # memberships
        ('make_member', '/make_member/{afm_id}'),
        ('merge_member', '/merge_member/{afm_id}/{mid}'),

        ('membership_listing_backend', '/memberships'),
        ('membership_listing_alphabetical', '/aml'),
        ('membership_listing_date_pdf', '/aml-{date}.pdf'),
        ('membership_listing_aufstockers', '/aml_aufstockers'),

        # Dues
        ('dues', '/dues'),

        # membership dues 2015
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
            '/dues15_reversal/{code}/C3S-dues15-{no}-S.pdf'),
        # for backward compatibility
        (
            'make_dues15_reversal_invoice_pdf_email',
            '/dues15_reversal/{email}/{code}/C3S-dues15-{no}-S.pdf'
        ),
        ('dues15_notice', '/dues15_notice/{member_id}'),
        ('dues15_listing', '/dues15_listing'),

        # membership dues 2016
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
            '/dues18_invoice/C3S-dues18-{i}.pdf'
        ),
        ('send_dues18_invoice_email', '/dues18_invoice/{member_id}'),
        ('send_dues18_invoice_batch', '/dues18_invoice_batch'),
        (
            'make_dues18_invoice_no_pdf',
            '/dues18_invoice_no/{code}/C3S-dues18-{i}.pdf'
        ),
        ('dues18_reduction', '/dues18_reduction/{member_id}'),

        (
            'dues18_reversal_pdf_backend',
            '/dues18_reversal/C3S-dues18-{i}-S.pdf'
        ),
        (
            'make_dues18_reversal_invoice_pdf',
            '/dues18_reversal/{code}/C3S-dues18-{no}-S.pdf'
        ),
        ('dues18_notice', '/dues18_notice/{member_id}'),
        ('dues18_listing', '/dues18_listing'),

        ('batch_archive_pdf_invoices', '/batch_archive_pdf_invoices'),

        # utilities & wizardry
        ('get_member', '/members/{member_id}'),
        ('error', '/error'),  # generic error view,

        # shares
        ('shares_detail', '/shares_detail/{id}'),
        ('shares_edit', '/shares_edit/{id}'),
        ('shares_delete', '/shares_delete/{id}'),

        # membership_certificate
        ('certificate_mail', '/cert_mail/{id}'),
        ('certificate_pdf', '/cert/{id}/C3S_{name}_{token}.pdf'),
        ('certificate_pdf_staff', '/cert/{id}/C3S_{name}.pdf'),

        # invite people
        ('invite_member', '/invite_member/{m_id}'),
        ('invite_batch', '/invite_batch/{number}'),

        # search for people
        ('search_people', '/search_people'),
        ('autocomplete_people_search', '/aps/'),

        # search for codes
        ('search_codes', '/search_codes'),
        ('autocomplete_input_values', '/aiv/'),

        ('payment_list', '/payments'),
        ('general_assembly', '/general-assembly'),
        ('annual_reporting', '/annual_reporting'),
    ]
    for route in routes:
        config.add_route(route[0], route[1])

    # applications for membership
    config.make_pagination_route(
        'dashboard',
        dashboard_content_size_provider,
        sort_property_default='id',
        page_size_default=int(
            settings.get('c3smembership.dashboard_number', 30)))

    # TODO: move application layer setup to separate module
    from c3smembership.data.repository.member_repository import (
        MemberRepository
    )
    from c3smembership.business.membership_application import (
        MembershipApplication
    )
    membership_application = MembershipApplication(MemberRepository)
    config.registry.membership_application = membership_application

    config.make_pagination_route(
        'membership_listing_backend',
        membership_content_size_provider,
        sort_property_default='id',
        page_size_default=int(
            settings.get('c3smembership.membership_number', 30)))

    # membership list
    from c3smembership.data.repository.member_repository import (
        MemberRepository
    )
    from c3smembership.business.member_information import MemberInformation
    config.registry.member_information = MemberInformation(MemberRepository)

    # TODO: move application layer setup to separate module
    from c3smembership.data.model.base import DBSession
    from c3smembership.data.model.base.c3smember import C3sMember
    from c3smembership.business.dues_invoice_archiving import (
        DuesInvoiceArchiving
    )
    from c3smembership.presentation.views.dues_2015 import (
        make_invoice_pdf_pdflatex,
        make_reversal_pdf_pdflatex,
    )
    invoices_archive_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../invoices/'))
    config.registry.dues_invoice_archiving = DuesInvoiceArchiving(
        DBSession,
        C3sMember,
        Dues15Invoice,
        make_invoice_pdf_pdflatex,
        make_reversal_pdf_pdflatex,
        invoices_archive_path)

    # Payments
    from c3smembership.data.repository.payment_repository import \
        PaymentRepository
    from c3smembership.business.payment_information import PaymentInformation
    config.registry.payment_information = PaymentInformation(
        PaymentRepository())

    from c3smembership.presentation.views.payment_list import \
        payment_content_size_provider
    config.make_pagination_route(
        'payment_list',
        payment_content_size_provider,
        sort_property_default='date',
        page_size_default=30)

    # General assembly
    from c3smembership.data.repository.general_assembly_repository import \
        GeneralAssemblyRepository
    from c3smembership.business.general_assembly_invitation import \
        GeneralAssemblyInvitation
    config.registry.general_assembly_invitation = GeneralAssemblyInvitation(
        GeneralAssemblyRepository())

    # annual reports
    from c3smembership.data.repository.share_repository import ShareRepository
    from c3smembership.business.share_information import ShareInformation
    config.registry.share_information = ShareInformation(ShareRepository)

    config.scan()
    return config.make_wsgi_app()
