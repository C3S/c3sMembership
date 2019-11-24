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
            ('general_assembly_create', '/general-assemblies/create'),
            ('general_assembly_edit', '/general-assemblies/{number}/edit'),
            ('general_assembly', '/general-assemblies/{number}'),
            (
                'general_assembly_invitation',
                '/general-assemblies/{number}/invite/{membership_number}'
            ),
            (
                'general_assembly_batch_invite',
                '/general-assemblies/{number}/batch-invite'
            ),
        ]
        self._add_routes(routes)
