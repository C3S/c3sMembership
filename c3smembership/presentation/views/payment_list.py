# -*- coding: utf-8 -*-
"""
Payment list view and payment content size provider for pagination.
"""

from pyramid.view import view_config

from c3smembership.data.repository.payment_repository import PaymentRepository
from c3smembership.business.payment_information import PaymentInformation


@view_config(renderer='../templates/payment_list.pt',
             permission='manage',
             route_name='payment_list')
def payment_list(request):
    """
    Payment list
    """
    payments = request.registry.payment_information.get_payments(
        request.pagination.paging.page_number,
        request.pagination.paging.page_size,
        request.pagination.sorting.sort_property,
        request.pagination.sorting.sort_direction,
    )
    return {'payments': payments}


def payment_content_size_provider(request):
    """
    Provides the payment content size, i.e. the number of payments available
    to be displayed.
    """
    return len(PaymentInformation(PaymentRepository()).get_payments(
        1,
        1000000000))
