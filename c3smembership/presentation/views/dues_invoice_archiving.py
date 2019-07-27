# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices
"""

from pyramid.view import view_config

from c3smembership.presentation.schemas.dues import create_archiving_form
from c3smembership.presentation.multiple_form_renderer import \
    MultipleFormRenderer


@view_config(
    route_name='batch_archive_pdf_invoices',
    renderer='c3smembership:presentation/templates/pages/invoice_archiving.pt')
def batch_archive_pdf_invoices(request):
    """
    Generate and archive a number of invoices

    Note:
        Expects the object request.registry.dues_invoice_archiving to implement
        c3smembership.business.dues_invoice_archiving.IDuesInvoiceArchiving.
    """
    form_renderer = build_form_renderer()
    result = {'invoices': []}
    return form_renderer.render(request, result)


def build_form_renderer():
    """
    Build the form renderer for the dues invoice archiving form
    """
    form_renderer = MultipleFormRenderer()
    form = create_archiving_form()
    form.formid = 'form'
    form_renderer.add_form(form, archive_invoices)
    return form_renderer


def archive_invoices(request, result, appstruct):
    """
    Archive the invoices
    """
    dues_invoice_archiving = request.registry.dues_invoice_archiving
    result['invoices'] = dues_invoice_archiving.generate_missing_invoice_pdfs(
        appstruct['count'])
    flash_message(request, result['invoices'], appstruct['count'])
    return result


def flash_message(request, generated_files, count):
    """
    Construct the message for invoice archiving to be displayed
    """
    if generated_files is not None:
        queue = 'success'
        if generated_files:
            message = 'Successfully archived {0} invoices.'.format(
                len(generated_files))
            if len(generated_files) == count:
                message += ' There might be more invoices to be archived.'
            else:
                message += ' There are no more invoices to be ' + \
                    'archived at the moment.'
        else:
            message = 'There were no invoices to be archived.'
    else:
        message = 'An error occurred during archiving the invoices.'
        queue = 'danger'
    request.session.flash(message, queue)
