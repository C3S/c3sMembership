"""
This module holds the error view.

It can be used from any other view, e.g. by way of redirection in case of
some error. Info stored in session can be displayed here (see template).
"""

from pyramid.view import view_config


@view_config(
    renderer='c3smembership.presentation:templates/pages/error.pt',
    route_name='error',
)
def error_view(request):
    """
    display error stored in session.
    """
    return {}
