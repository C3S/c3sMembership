# -*- coding: utf-8 -*-
"""
This module has functionality to let staff do administrative tasks.
"""

from datetime import datetime
import logging
from types import NoneType

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
        except ValidationFailure, error:
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
        except ValidationFailure, error:
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
    afmid = request.matchdict['member_id']
    afm = C3sMember.get_by_id(afmid)
    if isinstance(afm, NoneType):
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return get_dashboard_redirect(request)

    import random
    import string
    _looong_token = u''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(13))
    _url = (request.registry.settings['c3smembership.url'] +
            '/vae/' + afm.email_confirm_code +
            '/' + _looong_token + '/' + afm.email)

    _body = u'''[english version below]

Hallo {1} {2},

gemeinsam mit Dir freuen wir uns auf die erste Generalversammlung der C3S SCE
am 23. August, um 14:00 Uhr im Millowitsch-Theater in Köln. Details dazu
erhältst Du in Kürze in einer separaten Einladung.

Da wir die Einladungen per E-Mail verschicken werden, möchten wir Dich bitten
uns kurz zu bestätigen, dass diese E-Mail-Adresse korrekt ist und Du auf diesem
Wege erreichbar bist. Dafür brauchst Du nur den folgenden Link aufzurufen:

  {0}

Solltest Du nicht {1} {2} sein und diese Adresse nicht bei uns angegeben haben,
antworte bitte kurz auf diese E-Mail. Dann werden wir die Adresse aus unser
Datenbank streichen.

Antworte bitte ebenfalls, falls Du die E-Mail-Adresse ändern möchtest.


Viele Grüße :: Das C3S-Team

++++++++++++++++++++++++++++++++++++++++++++++++++

Hello {1} {2},

together with you we are happily awaiting the first general assembly of C3S SCE
on August 23rd, at 2 pm in the Millowitsch-Theater in Cologne. You will soon
receive the details in a separate invitation.

As we will send the invitations via email, we would like you to confirm your
email address beforehand.

Just click the following link to confirm your address:

    {0}

If you are not {1} {2} and you didn't give this email address to us, please
reply to this email with a short explanation. Then we will remove your address
from our database.

Should you want to change your email address please reply to this mail, too.

Best wishes :: The C3S Team
    '''.format(
        _url,  # {0}
        afm.firstname,  # {1}
        afm.lastname,  # {2}
    )

    LOG.info("mailing mail confirmation to AFM # %s", afm.id)

    message = Message(
        subject=(u'[C3S] Please confirm your email address! '
                 u'/ Bitte E-Mail-Adresse bestätigen!'),
        sender='yes@c3s.cc',
        recipients=[afm.email],
        body=_body
    )
    mailer = get_mailer(request)
    mailer.send(message)
    afm.email_confirm_token = _looong_token
    afm.email_confirm_mail_date = datetime.now()
    return get_dashboard_redirect(request, afm.id)
