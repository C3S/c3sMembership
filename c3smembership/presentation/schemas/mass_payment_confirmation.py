# -*- coding: utf-8 -*-
"""
Form and validation schemas for Mass Payment Confirmation.
"""

import datetime

import colander
import deform

from c3smembership.presentation.i18n import _


class MassPaymentConfirmation(colander.Schema):
    """
    Provides a colander schema for entering reference codes.
    """
    
    text = colander.SchemaNode(
        colander.String(),
        title=_('Reference Codes'),
        oid='text',
    )