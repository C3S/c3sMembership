# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices.
"""

from deform import ValidationFailure
from pyramid.view import view_config

from c3smembership.presentation.schemas.dues import create_archiving_form


@view_config(
    route_name='batch_archive_pdf_invoices',
    renderer='c3smembership:presentation/templates/pages/invoice_archiving.pt')
def batch_archive_pdf_invoices(request):
    """
    Generates and archives a number of invoices.

    The number of invoices is expected in request.POST['count']. If not
    specified all invoices are generated and archived.

    Note:
        Expects the object request.registry.dues_invoice_archiving to implement
        c3smembership.business.dues_invoice_archiving.IDuesInvoiceArchiving.
    """
    form = create_archiving_form()
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            dues_invoice_archiving = request.registry.dues_invoice_archiving
            count = appstruct['count']
            message = ''
            queue = ''
            generated_files = []
            if count is not None:
                generated_files = dues_invoice_archiving.generate_missing_invoice_pdfs(
                    count)
                if generated_files is not None:
                    queue = 'success'
                    if len(generated_files) == 0:
                        message = 'There were no invoices to be archived.'
                    if len(generated_files) > 0:
                        message = 'Successfully archived {0} invoices.'.format(
                            len(generated_files))
                        if len(generated_files) == count:
                            message += ' There might be more invoices to be archived.'
                        else:
                            message += ' There are no more invoices to be ' + \
                                'archived at the moment.'
                else:
                    message = 'An error occurred during archiving the invoices.'
                    queue = 'danger'

            request.session.flash(message, queue)
            return {
                'form': form.render(),
                'invoices': generated_files
            }
        except ValidationFailure as validationfailure:
            return {
                'form': validationfailure.render(),
                'invoices': [],
            }
    else:
        return {
            'form': form.render(),
            'invoices': [],
        }
