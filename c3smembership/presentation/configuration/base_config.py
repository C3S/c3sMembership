# -*- coding: utf-8 -*-
"""
Pyramid application base configuration.
"""

from pyramid_mailer import get_mailer

from c3smembership.security.request import RequestWithUserAttribute

from c3smembership.presentation.configuration import Configuration
from c3smembership.presentation.view_processing import FlashErrorHandler


class BaseConfig(Configuration):
    """
    Configuration base.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_includes()
        self.configure_subscribers()
        self.configure_registry()
        self.configure_routes()

    def configure_includes(self):
        """
        Configure basic Pyramid extension includes
        """
        includes = [
            'pyramid_mailer',
            'pyramid_chameleon',
            'cornice',
            'c3smembership.presentation.pagination',
            'c3smembership.presentation.view_processing',
        ]
        for include in includes:
            self.config.include(include)

    def configure_subscribers(self):
        """
        Configure basic Pyramid subscribers
        """
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
            self.config.add_subscriber(subscriber[0], subscriber[1])

    def configure_registry(self):
        """
        Configure the registry to contain the base.
        """
        self.config.set_request_factory(RequestWithUserAttribute)

        self.config.registry.get_mailer = get_mailer

        self.config.add_renderer(
            name='csv',
            factory='c3smembership.renderers.CSVRenderer')

        self.config.add_translation_dirs(
            'colander:locale/',
            'deform:locale/',
            'c3smembership:locale/')

        self.config.add_static_view('static_deform', 'deform:static')
        self.config.add_static_view(
            'static',
            'c3smembership:static',
            cache_max_age=3600)
        self.config.add_static_view(
            'docs',
            '../docs/_build/html/',
            cache_max_age=3600)

        self.config.set_colander_error_handler(FlashErrorHandler())

    def configure_routes(self):
        """
        Configure the base routes.
        """
        routes = [
            ('login', '/login'),
            ('logout', '/logout'),
            ('error', '/error'),
        ]
        self._add_routes(routes)
