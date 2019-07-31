# -*- coding: utf-8 -*-
"""
Delete a member record.

TODO: Must be restricted to deleting acquisitions. Once a member has acquired
membership it cannot simply be deleted but has to go through the membership
loss process.
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
    """

    deletion_confirmed = (request.params.get('deletion_confirmed', '0') == '1')
    redirection_view = request.params.get('redirect', 'dashboard')

    if deletion_confirmed:
        memberid = request.matchdict['memberid']
        member = C3sMember.get_by_id(memberid)

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
    else:
        request.session.flash(
            'Member does not exist and was not deleted.',
            'danger')
        return HTTPFound(request.route_url(redirection_view))
