# -*- coding: utf-8 -*-
"""
Gets member information in JSON format.
"""


from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound


@view_config(renderer='json',
             permission='manage',
             route_name='get_member')
def get_member(request):
    """
    Gets member information in JSON format for AJAX calls.
    """
    member_id = request.matchdict['member_id']
    member = request.registry.member_information.get_member_by_id(member_id)
    result = {}
    if member is not None:
        result = {
            'id': member.id,
            'firstname': member.firstname,
            'lastname': member.lastname
        }
    return result
