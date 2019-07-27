# -*- coding: utf-8 -*-
"""
Define schemas for membership dues.
"""

import colander
import deform
from c3smembership.presentation.i18n import _


class DuesInvoiceArchiving(colander.Schema):
    """
    Define the colander schema for dues invoice archiving
    """
    count = colander.SchemaNode(
        colander.Int(),
        title=_('Number of invoices to archive'),
    )


def create_archiving_form():
    """
    Create the dues invoice archiving form
    """
    return deform.Form(
        DuesInvoiceArchiving(),
        buttons=[deform.Button('submit', _(u'Archive invoices'))],
    )
