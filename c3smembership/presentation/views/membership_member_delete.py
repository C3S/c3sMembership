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
    LOG.info('redirect to: ' + str(redirection_view))

    if deletion_confirmed:
        memberid = request.matchdict['memberid']
        member = C3sMember.get_by_id(memberid)
        member_lastname = member.lastname
        member_firstname = member.firstname

        C3sMember.delete_by_id(member.id)
        LOG.info(
            "member.id %s was deleted by %s",
            member.id,
            request.user.login,
        )
        message = "member.id %s was deleted" % member.id
        request.session.flash(message, 'messages')

        msgstr = u'Member with id {0} \"{1}, {2}\" was deleted.'
        return HTTPFound(
            request.route_url(
                redirection_view,
                _query={'message': msgstr.format(
                    memberid,
                    member_lastname,
                    member_firstname)},
                _anchor='member_{id}'.format(id=str(memberid))
            )
        )
    else:
        return HTTPFound(
            request.route_url(
                redirection_view,
                _query={'message': (
                    'Deleting the member was not confirmed'
                    ' and therefore nothing has been deleted.')}
            )
        )
