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
        c3smembership.business.dues_invoice_archiving.DuesInvoiceArchiving.
    """
    form_renderer = build_form_renderer(request)
    result = {
        'generated_invoices': [],
        'archiving_stats': get_archiving_stats(request),
    }
    return form_renderer.render(request, result)


def get_archiving_stats(request):
    """
    Get statistics about archiving status for all years
    """
    return request.registry.dues_invoice_archiving.get_archiving_stats()


def build_form_renderer(request):
    """
    Build the form renderer for the dues invoice archiving form
    """
    form_renderer = MultipleFormRenderer()
    form = create_archiving_form(request)
    form.formid = 'form'
    form_renderer.add_form(form, archive_invoices)
    return form_renderer


def archive_invoices(request, result, appstruct):
    """
    Archive the invoices
    """
    dues_invoice_archiving = request.registry.dues_invoice_archiving
    result['generated_invoices'] = dues_invoice_archiving.generate_missing_invoice_pdfs(
        appstruct['archive_invoices']['year'],
        appstruct['archive_invoices']['count'])
    flash_message(
        request,
        result['generated_invoices'],
        appstruct['archive_invoices']['count'])

    # refresh as the initial set is not up-to-date anymore
    result['archiving_stats'] = get_archiving_stats(request)

    return result


def flash_message(request, generated_invoices, count):
    """
    Construct the message for invoice archiving to be displayed
    """
    if generated_invoices is not None:
        queue = 'success'
        if generated_invoices:
            message = 'Successfully archived {0} invoices.'.format(
                len(generated_invoices))
            if len(generated_invoices) == count:
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
