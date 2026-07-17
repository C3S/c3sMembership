# -*- coding: utf-8 -*-
"""
Delete a member record.

Deletion is restricted to datasets which have not been accepted as members,
i.e. membership applications (e.g. doublettes, test entries). Once a member
has acquired membership the dataset cannot be deleted but has to go through
the membership loss process and is subject to statutory retention periods.
"""

import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.data.model.base.c3smember import C3sMember


LOG = logging.getLogger(__name__)


@view_config(permission='manage',
             route_name='delete_entry')
def delete_entry(request):
    """
    This view lets accountants delete datasets (e.g. doublettes, test entries).

    Datasets of accepted members must not be deleted. They are subject to
    statutory retention (GenG, HGB, AO) and can only be ended via the
    membership loss process.
    """

    deletion_confirmed = (request.params.get('deletion_confirmed', '0') == '1')
    redirection_view = request.params.get('redirect', 'dashboard')

    if not deletion_confirmed:
        request.session.flash(
            'Deletion was not confirmed. No entry was deleted.',
            'danger')
        return HTTPFound(request.route_url(redirection_view))

    memberid = request.matchdict['memberid']
    member = C3sMember.get_by_id(memberid)

    if member is None:
        request.session.flash(
            'Member with id {} does not exist and was not deleted.'.format(
                memberid),
            'danger')
        return HTTPFound(request.route_url(redirection_view))

    if member.membership_accepted:
        LOG.warning(
            'deletion of member.id %s refused: membership accepted. '
            'Requested by %s.',
            member.id,
            request.user.login,
        )
        request.session.flash(
            'Member with id {} is an accepted member and was not deleted. '
            'Accepted members must go through the membership loss '
            'process.'.format(memberid),
            'danger')
        return HTTPFound(
            request.route_url(
                redirection_view,
                _anchor='member_{id}'.format(id=str(memberid))))

    C3sMember.delete_by_id(member.id)
    LOG.info(
        "member.id %s was deleted by %s",
        member.id,
        request.user.login,
    )
    message = "member.id %s was deleted" % member.id
    request.session.flash(message, 'success')

    return HTTPFound(
        request.route_url(
            redirection_view,
            _anchor='member_{id}'.format(id=str(memberid))))
