# -*- coding: utf-8 -*-
"""
Event handler for adding render information to all views
"""

import os

from pyramid.events import (
    subscriber,
    BeforeRender
)

from c3smembership.cache import cached
from c3smembership.git_tools import GitTools


# TODO: Version and message information must not be attached to all dictionary
# returning routes. Routes which only return json for auto completion must not
# contain this information. Find a proper mechanism to attach messages and
# versioning information to all necessary routes but not to all.


EXCLUDED_ROUTES = [
    'autocomplete_input_values',
    'autocomplete_people_search',
    'get_member',
]


@cached()
def get_version_information():
    """
    Get the version information including Git tag and branch
    """
    version_number = open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '../../',
        'VERSION')).read()

    tag = GitTools.get_tag()
    branch = GitTools.get_branch()

    version_metadata = [u'Version {0}'.format(version_number)]
    if tag is not None:
        version_metadata.append(u'Tag {0}'.format(tag))
    if branch is not None:
        version_metadata.append(u'Branch {0}'.format(branch))
    version_information = u', '.join(version_metadata)
    return version_information


@cached()
def get_version_location_name():
    """
    Get the version location name as the Git commit hash
    """
    return GitTools.get_commit_hash()


@cached()
def get_version_location_url():
    """
    Get the version location URL as the Git commit remote URL
    """
    return GitTools.get_github_commit_url()


@subscriber(BeforeRender)
def version_before_render(event):
    """
    Add version information to the renderer

    Version information includes the Git tag, branch and commit and remote URL.
    """
    if isinstance(event.rendering_val, dict):
        request = event.get('request')
        if request.matched_route is not None \
                and request.matched_route.name not in EXCLUDED_ROUTES:

            event.rendering_val['version_information'] = \
                get_version_information()
            event.rendering_val['version_location_name'] = \
                get_version_location_name()
            event.rendering_val['version_location_url'] = \
                get_version_location_url()
