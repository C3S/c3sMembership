# -*- coding: utf-8 -*-
"""
Login
"""

import logging

import deform
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound
from pyramid.security import (
    authenticated_userid,
    forget,
    remember,
)
from pyramid.url import route_url
from pyramid.view import view_config

from c3smembership.data.model.base.staff import Staff
from c3smembership.presentation.i18n import _
from c3smembership.presentation.schemas.accountant_login import (
    AccountantLogin
)
from c3smembership.presentation.views.membership_acquisition import (
    get_dashboard_redirect,
)


LOG = logging.getLogger(__name__)


@view_config(
    renderer='c3smembership.presentation:templates/pages/login.pt',
    route_name='login')
def login(request):
    """
    This view lets accountants log in (using a login form).

    If a person is already logged in, she is forwarded to the dashboard.
    """
    logged_in = authenticated_userid(request)

    LOG.info("login by %s", logged_in)

    if logged_in is not None:
        return get_dashboard_redirect(request)

    form = deform.Form(
        AccountantLogin(),
        buttons=[
            deform.Button('submit', _(u'Submit')),
            deform.Button('reset', _(u'Reset'))
        ],
    )

    # if the form has been used and SUBMITTED, check contents
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e_validation_failure:
            request.session.flash(
                _(u"Please note: There were errors, "
                  "please check the form below."),
                'message_above_form',
                allow_duplicate=False)
            return{'form': e_validation_failure.render()}

        # get user and check pw...
        username = appstruct['login']
        password = appstruct['password']

        try:
            checked = Staff.check_password(username, password)
        except AttributeError:  # pragma: no cover
            checked = False
        if checked:
            LOG.info("password check for %s: good!", username)
            headers = remember(request, username)
            LOG.info("logging in %s", username)
            return HTTPFound(
                request.route_url(
                    'dashboard'),
                headers=headers)
        else:
            LOG.info("password check: failed for %s.", username)
    else:
        request.session.pop('message_above_form')

    html = form.render()
    return {'form': html, }


@view_config(permission='view',
             route_name='logout')
def logout(request):
    """
    Is used to log a user/staffer off. "forget"
    """
    request.session.invalidate()
    request.session.flash(u'Logged out successfully.')
    headers = forget(request)
    return HTTPFound(
        location=route_url('login', request),
        headers=headers
    )
