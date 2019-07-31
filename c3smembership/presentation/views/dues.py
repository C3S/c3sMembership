# -*- coding: utf-8 -*-
"""
Dues view
"""


from pyramid.view import view_config


@view_config(renderer='c3smembership.presentation:templates/pages/dues.pt',
             permission='manage',
             route_name='dues')
def dues(request):  # pragma: no cover
    """
    Show the dues page
    """
    # pylint: disable=unused-argument
    return {}
