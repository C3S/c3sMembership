# -*- coding: utf-8 -*-
"""
Pyramid application configuration for statistics.
"""

from c3smembership.presentation.configuration import Configuration


class StatisticsConfig(Configuration):
    """
    Configuration for statistics.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()

    def configure_routes(self):
        """
        Configure the statistics routes.
        """
        routes = [
            ('stats', '/stats'),
        ]
        self._add_routes(routes)
