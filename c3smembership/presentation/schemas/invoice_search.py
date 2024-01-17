# -*- coding: utf-8 -*-
"""
Form and validation schemas for Mass Payment Confirmation.
"""

import colander
import deform

from c3smembership.presentation.i18n import _

# --- Fields ------------------------------------------------------------------

class InvoiceSearch(colander.Schema):
    """
    Provides a colander schema for entering reference codes.
    """

    invoicecode = colander.SchemaNode(
        colander.String(),
        title=_('Invoice Code'),
        oid='invoicecode',
        validator=colander.Regex('^(C3S-dues)?[0-9]{4}-[0-9]{4}$',
                                 'Muss dem Schema "2024-1234" oder '
                                 '"C3S-dues2024-1234" entsprechen.')
    )
