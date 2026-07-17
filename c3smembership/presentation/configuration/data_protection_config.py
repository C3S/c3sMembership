# -*- coding: utf-8 -*-
"""
Pyramid application configuration for data protection.
"""

from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.data.repository.member_repository import MemberRepository

from c3smembership.business.data_protection import DataProtection

from c3smembership.presentation.configuration import Configuration


class DataProtectionConfig(Configuration):
    """
    Configuration for data protection.

    Must be configured after DuesConfig because the data protection
    business layer uses the dues invoice archiving object from the
    registry to remove archived invoice PDF files.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the data protection business
        layer.
        """
        self.config.registry.data_protection = DataProtection(
            MemberRepository,
            DuesInvoiceRepository,
            self.config.registry.dues_invoice_archiving)

    def configure_routes(self):
        """
        Configure the data protection routes.
        """
        routes = [
            ('data_protection', '/data_protection'),
        ]
        self._add_routes(routes)
