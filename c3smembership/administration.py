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
from c3smembership.models import (
    C3sMember,
    C3sStaff,
    Group,
)
from c3smembership.presentation.views.dashboard import get_dashboard_redirect
from c3smembership.views.afm import send_mail_confirmation_mail


DEBUG = False
LOGGING = True

LOG = logging.getLogger(__name__)


@view_config(renderer='templates/staff.pt',
             permission='manage',
             route_name='staff')
def staff_view(request):
    """
    This view lets admins edit staff personnel.

    - edit/change password
    - delete
    """
    _staffers = C3sStaff.get_all()

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
            _staffer = C3sStaff.get_by_id(int(request.POST['id']))
        except (KeyError, ValueError):
            return HTTPFound(location=request.route_url('staff'))
        if request.POST['action'] == u'delete':
            C3sStaff.delete_by_id(_staffer.id)
            encrypted = encrypt_with_gnupg('''hi,
%s was deleted from the backend by %s.

best,
your membership tool''' % (_staffer.login,
                           authenticated_userid(request)))
            message = Message(
                subject='[C3S Yes] staff was deleted.',
                sender='noreply@c3s.cc',
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
        except ValidationFailure as error:
            return {
                'stafferform': error.render()
            }
        existing = C3sStaff.get_by_login(appstruct['login'])
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
                sender='noreply@c3s.cc',
                recipients=[
                    request.registry.settings['c3smembership.mailaddr']],
                body=encrypted
            )

        else:  # create new entry
            staffer = C3sStaff(
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
                sender='noreply@c3s.cc',
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


@view_config(renderer='templates/delete_afms.pt',
             permission='manage',
             route_name='delete_afms')
def delete_afms(request):
    '''
    Delete a bunch of AfMs in one go.

    I wrote this while implementing mass import to ease development 8-)
    '''
    class DeleteAfMRange(colander.MappingSchema):
        """
        Schema for deleting a range of membership applications
        """
        first = colander.SchemaNode(
            colander.Integer(),
            title='first ID to delete'
        )
        last = colander.SchemaNode(
            colander.Integer(),
            title='last ID to delete'
        )
    schema = DeleteAfMRange()
    delete_range_form = deform.Form(
        schema,
        buttons=[deform.Button('delete_them', 'DELETE')]
    )
    if 'first' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = delete_range_form.validate(controls)
            _first = appstruct['first']
            _last = appstruct['last']
            # pylint: disable=superfluous-parens
            assert(_first < _last)
        except ValidationFailure as error:
            return {
                'resetform': error.render()
            }
        for i in range(_first, _last+1):
            C3sMember.delete_by_id(i)
        return HTTPFound(request.route_url('dashboard'))
    return {
        'delete_form': delete_range_form.render()
    }


@view_config(permission='manage',
             route_name='mail_mail_confirmation')
def mail_mail_conf(request):
    '''
    Send email to member to confirm her email address by clicking a link.

    Needed for applications that came in solely on paper
    and were digitalized/entered into DB by staff.
    '''
    member_id = request.matchdict['member_id']
    member = C3sMember.get_by_id(member_id)
    if member is None:
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return get_dashboard_redirect(request)

    send_mail_confirmation_mail(
        member,
        request.registry.settings['c3smembership.url'],
        request.registry.get_mailer(request),
        request.localizer,
        request.registry.settings['testing.mail_to_console'])

    return get_dashboard_redirect(request, member.id)
