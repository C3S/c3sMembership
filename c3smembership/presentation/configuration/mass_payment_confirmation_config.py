# -*- coding: utf-8 -*-
"""
Pyramid application configuration for mass payment confirmation.
"""

from c3smembership.presentation.configuration import Configuration


class MassPaymentCofirmationConfig(Configuration):
    """
    Configuration for annual reporting.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()

    def configure_routes(self):
        """
        Configure the mass payment confirmation routes.
        """
        routes = [
            ('mass_payment_confirmation',
             '/mass_payment_confirmation'),
        ]
        self._add_routes(routes)
