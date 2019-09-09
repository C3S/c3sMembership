# -*- coding: utf-8 -*-
"""
Define schemas for membership dues.
"""

import colander
import deform

from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)


@colander.deferred
def invoice_archiving_year_widget(node, keywords):
    """
    Get the deferred year widget
    """
    # pylint: disable=unused-argument
    return deform.widget.SelectWidget(
        values=keywords.get('years'))


class InvoiceArchivingSchema(colander.MappingSchema):
    """
    Define the colander schema for dues invoice archiving
    """
    year = colander.SchemaNode(
        colander.Int(),
        title=_('Year to archive invoices of'),
        widget=invoice_archiving_year_widget,
        oid='year',
    )
    count = colander.SchemaNode(
        colander.Int(),
        validator=colander.Range(min=1),
        title=_('Number of invoices to archive'),
        default=20,
        oid='count',
    )


def create_archiving_form(request):
    """
    Create the dues invoice archiving form
    """
    configured_years = request.registry.dues_invoice_archiving.get_configured_years()
    select_years = [(year, year) for year in configured_years]

    class InvoiceArchivingSchemaGroup(colander.Schema):
        """
        Invoice archiving schema group

        Provide a box and a title to the schema
        """
        archive_invoices = InvoiceArchivingSchema(
            title=_('Archive invoices')
        ).bind(years=select_years)

    return deform.Form(
        InvoiceArchivingSchemaGroup(),
        buttons=[deform.Button('submit', _(u'Archive invoices'))],
        renderer=ZPT_RENDERER
    )
