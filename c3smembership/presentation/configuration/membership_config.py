# -*- coding: utf-8 -*-
"""
Pyramid application configuration for membership.
"""

from c3smembership.data.repository.member_repository import (
    MemberRepository
)
from c3smembership.business.member_information import MemberInformation
from c3smembership.presentation.views.membership_listing import (
    membership_content_size_provider
)

from c3smembership.presentation.configuration import Configuration


class MembershipConfig(Configuration):
    """
    Configuration for membership.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the membership business
        layer.
        """
        self.config.registry.member_information = MemberInformation(
            MemberRepository)

        self.config.make_pagination_route(
            'membership_listing_backend',
            membership_content_size_provider,
            sort_property_default='id',
            page_size_default=int(
                self.config.get_settings().get(
                    'c3smembership.membership_number', 30)))

    def configure_routes(self):
        """
        Configure the membership routes.
        """
        routes = [
            ('toolbox', '/membership-tools'),
            ('detail', '/detail/{memberid}'),
            ('edit', '/edit/{_id}'),
            ('member_details', '/members/{membership_number}'),
            ('get_member', '/members/{member_id}'),

            # listings
            ('membership_listing_backend', '/memberships'),
            ('membership_listing_alphabetical', '/aml'),
            ('membership_listing_date_pdf', '/aml-{date}.pdf'),
            ('membership_listing_aufstockers', '/aml_aufstockers'),

            # membership_certificate
            ('certificate_mail', '/cert_mail/{id}'),
            ('certificate_pdf', '/cert/{id}/C3S_{name}_{token}.pdf'),
            ('certificate_pdf_staff', '/cert/{id}/C3S_{name}.pdf'),

            # search for people
            ('search_people', '/search_people'),
            ('autocomplete_people_search', '/aps/'),

            # search for codes
            ('search_codes', '/search_codes'),
            ('autocomplete_input_values', '/aiv/'),
        ]
        self._add_routes(routes)
