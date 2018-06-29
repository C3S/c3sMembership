# -*- coding: utf-8 -*-
import colander
import deform
from c3smembership.presentation.i18n import _


class AccountantLogin(colander.MappingSchema):
    """
    colander schema for login form
    """
    login = colander.SchemaNode(
        colander.String(),
        title=_(u"Username"),
        oid="login")
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=deform.widget.PasswordWidget(size=20),
        title=_(u"Password"),
        oid="password")
