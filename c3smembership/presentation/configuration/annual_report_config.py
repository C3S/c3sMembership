# -*- coding: utf-8 -*-
"""
Pyramid application configuration for annual reporting.
"""

from c3smembership.data.repository.share_repository import ShareRepository
from c3smembership.business.share_information import ShareInformation

from c3smembership.presentation.configuration import Configuration


class AnnualReportConfig(Configuration):
    """
    Configuration for annual reporting.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the annual reporting business layer.
        """
        self.config.registry.share_information = ShareInformation(
            ShareRepository)

    def configure_routes(self):
        """
        Configure the annual reporting routes.
        """
        routes = [
            ('annual_reporting', '/annual_reporting'),
        ]
        self._add_routes(routes)
