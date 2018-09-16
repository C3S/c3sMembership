# -*- coding: utf-8 -*-
"""
Pyramid application configuration for staff.
"""

from c3smembership.presentation.configuration import Configuration


class StaffConfig(Configuration):
    """
    Configuration for staff.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()

    def configure_routes(self):
        """
        Configure the staff routes.
        """
        routes = [
            ('staff', '/staff'),
        ]
        self._add_routes(routes)
