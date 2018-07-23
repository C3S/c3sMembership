# -*- coding: utf-8 -*-
"""
This module has functionality to let staff do administrative tasks.
"""

from datetime import datetime
import logging

import colander
import deform
from deform import ValidationFailure
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid

from c3smembership.data.model.base import DBSession
from c3smembership.gnupg_encrypt import encrypt_with_gnupg
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


DEBUG = False
LOGGING = True

LOG = logging.getLogger(__name__)


@view_config(
    renderer='c3smembership.presentation:templates/pages/staff.pt',
    permission='manage',
    route_name='staff')
def staff_view(request):
    """
    This view lets admins edit staff personnel.

    - edit/change password
    - delete
    """
    _staffers = Staff.get_all()

    class Staffer(colander.MappingSchema):
        """
        Staff login schema
        """
        login = colander.SchemaNode(
            colander.String(),
            title='login',
        )
        password = colander.SchemaNode(
            colander.String(),
            title='passwort',
        )

    schema = Staffer()

    stafferform = deform.Form(
        schema,
        buttons=[
            deform.Button('new_staffer', 'save')
        ]
    )

    if 'action' in request.POST:
        try:
            _staffer = Staff.get_by_id(int(request.POST['id']))
        except (KeyError, ValueError):
            return HTTPFound(location=request.route_url('staff'))
        if request.POST['action'] == u'delete':
            Staff.delete_by_id(_staffer.id)
            encrypted = encrypt_with_gnupg('''hi,
%s was deleted from the backend by %s.

best,
your membership tool''' % (_staffer.login,
                           authenticated_userid(request)))
            message = Message(
                subject='[C3S Yes] staff was deleted.',
                sender='yes@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )
            mailer = get_mailer(request)
            mailer.send(message)
            return HTTPFound(location=request.route_url('staff'))
        elif request.POST['action'] == 'edit':
            appstruct = {
                'login': _staffer.login,
                'password': '_UNCHANGED_',
            }
            stafferform.set_appstruct(appstruct)

    if 'new_staffer' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = stafferform.validate(controls)
        except ValidationFailure, error:
            return {
                'stafferform': error.render()
            }
        existing = Staff.get_by_login(appstruct['login'])
        if existing is not None:
            if u'_UNCHANGED_' in appstruct['password']:
                pass
            else:
                existing.password = appstruct['password']
                existing.last_password_change = datetime.now()
            encrypted = encrypt_with_gnupg('''hi,
the password of %s was changed by %s.

best,
your membership tool''' % (existing.login,
                           authenticated_userid(request)))
            message = Message(
                subject='[C3S Yes] staff password changed.',
                sender='yes@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )

        else:  # create new entry
            staffer = Staff(
                login=appstruct['login'],
                password=appstruct['password'],
                email=u'',
            )
            staffer.groups = [Group.get_staffers_group()]
            # pylint: disable=no-member
            DBSession.add(staffer)
            DBSession.flush()
            encrypted = encrypt_with_gnupg('''hi,
%s was added to the backend by %s.

best,
your membership tool''' % (staffer.login,
                           authenticated_userid(request)))
            message = Message(
                subject='[C3S Yes] staff was added.',
                sender='yes@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )
            mailer = get_mailer(request)
            mailer.send(message)

        return HTTPFound(
            request.route_url('staff')
        )

    return {
        'staffers': _staffers,
        'stafferform': stafferform.render(),
    }
