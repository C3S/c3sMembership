# -*- coding: utf-8 -*-

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from c3smembership.data.model.base.c3smember import C3sMember


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

    general_assembly_invitation = request.registry.general_assembly_invitation

    latest_general_assembly = general_assembly_invitation \
        .get_latest_general_assembly()

    invitations = None
    if latest_general_assembly is not None:
        invitations = {}
        for membership in memberships:
            invitations[membership.membership_number] = \
                general_assembly_invitation.get_member_invitation(
                    membership,
                    latest_general_assembly.number)

    return {
        'members': memberships,
        'invitations': invitations,
        'latest_general_assembly': latest_general_assembly,
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
    if type(member_id) == str:
        member_id_str = member_id
    else:
        member_id_str = str(member_id)
    if len(member_id_str) > 0:
        anchor['_anchor'] = 'member_{id}'.format(id=member_id_str)

    return HTTPFound(request.route_url('membership_listing_backend', **anchor))
