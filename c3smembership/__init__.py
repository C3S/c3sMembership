# -*- coding: utf-8 -*-
"""
This module holds the main method: config and route declarations
"""

import os

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from sqlalchemy import engine_from_config

from c3smembership.data.model.base import Base
from c3smembership.security import (
    Root,
    groupfinder
)

from c3smembership.presentation.configuration.annual_report_config import \
    AnnualReportConfig
from c3smembership.presentation.configuration.base_config import \
    BaseConfig
from c3smembership.presentation.configuration.dues_config import DuesConfig
from c3smembership.presentation.configuration.general_assembly_config import \
    GeneralAssemblyConfig
from c3smembership.presentation.configuration.membership_config import \
    MembershipConfig
from c3smembership.presentation.configuration.membership_application_config \
    import MembershipApplicationConfig
from c3smembership.presentation.configuration.share_config \
    import ShareConfig
from c3smembership.presentation.configuration.staff_config import StaffConfig
from c3smembership.presentation.configuration.statistics_config import \
    StatisticsConfig

# Import for SqlAlchemy metadata detection. Currently, the metadata detection
# only covers some of the tables probably because they are imported here.
# Others are not covered maybe because they are not directly imported but only
# through view discovery. There might be a better and cleaner solution to this
# problem but hasn't been discovered yet.
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice
from c3smembership.data.model.base.general_assembly import GeneralAssembly
from c3smembership.data.model.base.general_assembly_invitation import \
    GeneralAssemblyInvitation


__version__ = open(os.path.join(os.path.abspath(
    os.path.dirname(__file__)), '../VERSION')).read()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.bind = engine

    session_factory = session_factory_from_settings(settings)
    authn_policy = AuthTktAuthenticationPolicy(
        's0secret!!',
        callback=groupfinder,)
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy,
                          session_factory=session_factory,
                          root_factory=Root)

    module_configs = [
        BaseConfig,
        MembershipConfig,
        MembershipApplicationConfig,
        ShareConfig,
        AnnualReportConfig,
        DuesConfig,
        GeneralAssemblyConfig,
        StatisticsConfig,
        StaffConfig,
    ]
    for module_config in module_configs:
        module_config(config).configure()

    config.scan()
    return config.make_wsgi_app()
