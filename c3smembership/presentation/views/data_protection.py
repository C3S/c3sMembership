# -*- coding: utf-8 -*-
"""
Data protection retention review.

Shows the datasets whose retention period has expired (members who lost
membership past the statutory retention periods and stale, never
completed membership applications) and lets staff anonymize them, see
c3smembership.business.data_protection.

Anonymization is staff-triggered with a confirmation step so that a
human stays in the loop.
"""

import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.business.data_protection import (
    APPLICATION_RETENTION_MONTHS,
    DataProtection,
    MEMBER_RETENTION_YEARS,
    NotAnErasureCandidateError,
)


LOG = logging.getLogger(__name__)


def _anonymize_selected(request):
    """
    Anonymize the datasets selected in the submitted form.

    Requires the confirmation flag to be set by the confirmation dialog.
    Flashes a summary of how many datasets were anonymized and how many
    were refused.
    """
    confirmed = (
        request.POST.get('anonymization_confirmed', '0') == '1')
    member_ids = request.POST.getall('member_id')

    if not confirmed:
        request.session.flash(
            'Anonymization was not confirmed. No dataset was anonymized.',
            'danger')
        return

    if not member_ids:
        request.session.flash(
            'No datasets were selected for anonymization.',
            'danger')
        return

    data_protection = request.registry.data_protection
    anonymized_count = 0
    refused_count = 0
    for member_id in member_ids:
        try:
            data_protection.anonymize_member(
                int(member_id), request.user.login)
            anonymized_count += 1
        except (NotAnErasureCandidateError, ValueError):
            refused_count += 1

    if anonymized_count > 0:
        request.session.flash(
            '{} dataset(s) were anonymized.'.format(anonymized_count),
            'success')
    if refused_count > 0:
        request.session.flash(
            '{} dataset(s) were refused because they are not erasure '
            'candidates.'.format(refused_count),
            'danger')


@view_config(
    permission='manage',
    route_name='data_protection',
    renderer='c3smembership.presentation:templates/pages/'
             'data_protection.pt')
def data_protection_view(request):
    """
    Render the retention review page and handle anonymization requests.
    """
    if request.method == 'POST':
        _anonymize_selected(request)
        return HTTPFound(request.route_url('data_protection'))

    candidates = request.registry.data_protection.get_erasure_candidates()
    return {
        'lost_members': candidates['lost_members'],
        'stale_applications': candidates['stale_applications'],
        'member_retention_years': MEMBER_RETENTION_YEARS,
        'application_retention_months': APPLICATION_RETENTION_MONTHS,
        'member_retention_cutoff':
            DataProtection.get_member_retention_cutoff(),
        'application_retention_cutoff':
            DataProtection.get_application_retention_cutoff(),
    }
