# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices.
"""

from pyramid.view import view_config

from c3smembership.business.dues_invoice_archiving import DuesInvoiceArchiving


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
    dues_invoice_archiving = request.registry.dues_invoice_archiving
    count = float('inf')
    status = 'succeeded'
    message = ''
    generated_files = []
    if 'count' in request.POST:
        try:
            count = int(request.POST['count'])
        except ValueError:
            status = 'failed-count'
    if status == 'succeeded':
        generated_files = dues_invoice_archiving.generate_missing_invoice_pdfs(
            count)
        if generated_files is not None:
            status = 'succeeded'
        else:
            status = 'failed-generation'
    return {
        'count': count,
        'status': status,
        'archiving_message': message,
        'invoices': generated_files
    }
