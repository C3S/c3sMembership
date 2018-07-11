# -*- coding: utf-8 -*-
"""
Dues view.
"""


from pyramid.view import view_config


@view_config(renderer='../templates/dues.pt',
             permission='manage',
             route_name='dues')
def dues(request):
    return {}
