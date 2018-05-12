# -*- coding: utf-8 -*-
"""
Dashboard view showing membership applicants.
"""


from c3smembership.models import (
    C3sMember,
    InvalidPropertyException,
    InvalidSortDirection,
)
from c3smembership.presentation.parameter_validation import (
    ParameterValidationException,
)
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound


@view_config(renderer='../templates/dashboard.pt',
             permission='manage',
             route_name='dashboard')
def dashboard(request):
    """
    The Dashboard.

    This view lets accountants view
    the **list of applications for membership**.

    Some details can be seen (name, email, link to more details)
    as well as their membership application *progress*:

    - has their signature arrived?
    - how about the payment?
    - have reminders been sent? receptions confirmed?

    There are also links to *edit* or *delete* one of the datasets.

    Once all requirements are fulfilled,
    an application can be turned into a membership from here:
    a button shows up.
    """

    pagination = request.pagination
    try:
        members = C3sMember.nonmember_listing(
            pagination.paging.content_offset,
            pagination.paging.page_size,
            pagination.sorting.sort_property,
            pagination.sorting.sort_direction)
    except (InvalidPropertyException, InvalidSortDirection):
        raise ParameterValidationException(
            'Page does not exist.',
            request.route_url(request.matched_route.name))
    return {
        'members': members,
    }


def dashboard_content_size_provider():
    # TODO: Architectural cleanup necessary as the presentation layer
    # is directly accessing the data layer. It should instead access the
    # business layer.
    return C3sMember.nonmember_listing_count()


def get_dashboard_redirect(request, member_id=''):
    """Get the redirect for the dashboard.

    Gets an HTTPFound for redirection to the dashboard including passing page
    number and sorting information from cookies as well as setting an anchor
    on the member identified by member_id.

    Args:
        request: The request which is being processed.
        member_id: Optional value of a member on which to set an anchor in the
            redirection.

    Returns:
        A HTTPFound for redirection to the dashboard.
    """
    kwargs = {}
    member_id_str = str(member_id)
    if len(member_id_str) > 0:
        kwargs['_anchor'] = 'member_{id}'.format(id=member_id_str)

    return HTTPFound(request.route_url('dashboard', **kwargs))
