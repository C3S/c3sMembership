# -*- coding: utf-8 -*-
"""
Pyramid application configuration.
"""


class Configuration(object):
    """
    Base class for Pyramid configuration
    """

    def __init__(self, config):
        """
        Initialise the Configuration object.
        """
        self.config = config

    def _add_routes(self, routes):
        """
        Add the routes to the configuration.

        Args:
            routes: An array of tuples containing of route name and route
                pattern which are added to the configuration
        """
        for route in routes:
            self.config.add_route(route[0], route[1])

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.

        Args:
            config: The pyramid.config.Configurator object to which the routes
                are added.
        """
        raise NotImplementedError()
