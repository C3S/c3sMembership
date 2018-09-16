# -*- coding: utf-8 -*-
"""
Pyramid application configuration for shares.
"""

from c3smembership.data.repository.share_repository import ShareRepository
from c3smembership.business.share_acquisition import ShareAcquisition

from c3smembership.presentation.configuration import Configuration


class ShareConfig(Configuration):
    """
    Configuration for shares.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the share business layer.
        """
        share_acquisition = ShareAcquisition(ShareRepository)
        self.config.registry.share_acquisition = share_acquisition

    def configure_routes(self):
        """
        Configure the share routes.
        """
        routes = [
            # shares
            ('shares_detail', '/shares_detail/{id}'),
            ('shares_edit', '/shares_edit/{id}'),
            ('shares_delete', '/shares_delete/{id}'),
        ]
        self._add_routes(routes)
