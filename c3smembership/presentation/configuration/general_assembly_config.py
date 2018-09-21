# -*- coding: utf-8 -*-
"""
Pyramid application configuration for general assembly invitations.
"""

from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository

from c3smembership.business.general_assembly_invitation import \
    GeneralAssemblyInvitation

from c3smembership.presentation.configuration import Configuration


class GeneralAssemblyConfig(Configuration):
    """
    Configuration for general assembly invitations.
    """

    def configure(self):
        """
        Add the configuration of the module to the Pyramid configuration.
        """
        self.configure_routes()
        self.configure_registry()

    def configure_registry(self):
        """
        Configure the registry to contain the general assembly business layer.
        """
        self.config.registry.general_assembly_invitation = \
            GeneralAssemblyInvitation(GeneralAssemblyRepository())

    def configure_routes(self):
        """
        Configure the general assembly invitation routes.
        """
        routes = [
            ('general_assemblies', '/general-assemblies'),
            ('invite_member', '/invite_member/{m_id}'),
            ('invite_batch', '/invite_batch/{number}'),
        ]
        self._add_routes(routes)
