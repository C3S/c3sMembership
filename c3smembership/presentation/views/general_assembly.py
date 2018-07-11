# -*- coding: utf-8 -*-
"""
General assembly view.
"""


from pyramid.view import view_config


@view_config(renderer='../templates/general_assembly.pt',
             permission='manage',
             route_name='general_assembly')
def general_assembly(request):
    return {}
