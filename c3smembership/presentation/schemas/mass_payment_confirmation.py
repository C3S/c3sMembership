# -*- coding: utf-8 -*-
"""
Form and validation schemas for Mass Payment Confirmation.
"""

import datetime

import colander
import deform

from c3smembership.presentation.i18n import _

# --- Validators --------------------------------------------------------------


def is_csv(value):
    """Ensure this looks like a valid reduced Hibiscus csv."""

    csvhdr = ("\"Datum\";\"Gegenkonto Inhaber\";\"Verwendungszwecke\";"
              "\"Betrag\";\"Rechnungscode\"")
    csvhdrlen = len(csvhdr)
    if not value or len(value) < csvhdrlen or value[:csvhdrlen] != csvhdr:
        return _("Please paste a reduced Hibiscus CSV export "
                 f"in the form {csvhdr} here.")
    return True


# --- Fields ------------------------------------------------------------------

class MassPaymentConfirmation(colander.Schema):
    """
    Provides a colander schema for entering reference codes.
    """

    text = colander.SchemaNode(
        colander.String(),
        title=_('Reference Codes'),
        oid='text',
        widget=deform.widget.TextAreaWidget(),
        validator=colander.Function(is_csv)
    )
