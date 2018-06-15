# -*- coding: utf-8 -*-
"""
Defines the schema for the payment list filters.
"""

import colander
import deform

from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)


class PaymentListFilterSchema(colander.Schema):
    """
    The schema for payment list filters.
    """

    from_date = colander.SchemaNode(
        colander.Date(),
        title=_(u"From date"),
        missing=None,
        oid="from_date",
    )
    to_date = colander.SchemaNode(
        colander.Date(),
        title=_(u"To date"),
        missing=None,
        oid="from_date",
    )


def create_payment_filter_form():
    filter_schema = PaymentListFilterSchema()
    filter_form = deform.Form(
        filter_schema,
        buttons=[
            deform.Button('submit', _(u'Apply')),
            deform.Button('reset', _(u'Reset')),
        ],
        use_ajax=True,
        renderer=ZPT_RENDERER
    )
    return filter_form
