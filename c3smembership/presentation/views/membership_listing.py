# -*- coding: utf-8 -*-

from c3smembership.models import C3sMember
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_members.pt',
    permission='manage',
    route_name='membership_listing_backend')
def membership_listing_backend(request):
    """
    This view lets accountants view all members.

    the list is HTML with clickable links,
    not good for printout.
    """
    memberships = C3sMember.get_members(
        request.pagination.sorting.sort_property,
        how_many=request.pagination.paging.page_size,
        offset=request.pagination.paging.content_offset,
        order=request.pagination.sorting.sort_direction)
    return {
        'members': memberships,
    }


def membership_content_size_provider(request):
    return C3sMember.get_num_members_accepted()


def get_memberhip_listing_redirect(request, member_id=''):
    """Get the redirect for the dashboard.

    Gets an HTTPFound for redirection to the dashboard including passing page
    number and sorting information from cookies as well as setting an anchor
    on the member identified by member_id.

    Args:
        request: The request which is being processed.
        member_id: Optional value of a member on which to set an anchor in the
            redirection.

    Returns:
        A HTTPFound for redirection to the membership listing.
    """
    anchor = {}
    if type(member_id) == str or type(member_id) == unicode:
        member_id_str = member_id
    else:
        member_id_str = str(member_id)
    if len(member_id_str) > 0:
        anchor['_anchor'] = 'member_{id}'.format(id=member_id_str)

    return HTTPFound(request.route_url('membership_listing_backend', **anchor))
