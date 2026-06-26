# -*- coding: utf-8 -*-
"""
Dues view
"""

from datetime import date
import os

from pyramid.view import view_config

from c3smembership.presentation.views import dues_year
from c3smembership.presentation.views.dues_year import (
    DUES_YEARS,
    LATEST_DUES_YEAR,
)

# the LaTeX template kinds which must exist for a dues year to be usable
_TEMPLATE_KINDS = ('invoice_de', 'invoice_en', 'storno_de', 'storno_en')


def next_year_status(request, today=None):
    """
    Determine whether a not-yet-configured dues year has begun.

    A new dues year is the year following ``LATEST_DUES_YEAR``. It is considered
    to have begun once the current date is in that year or later. In that case
    the LaTeX invoice templates are checked for presence so that staff know
    whether enabling the year only requires bumping ``LATEST_DUES_YEAR`` and
    redeploying.

    Args:
        request: The Pyramid request, used to read the certificate template.
        today: Optional date used as "now"; defaults to ``date.today()``.

    Returns:
        ``None`` if no new dues year has begun yet, otherwise a dict with the
        new year, whether its templates are present and which are missing.
    """
    if today is None:
        today = date.today()
    if today.year <= LATEST_DUES_YEAR:
        return None

    next_year = LATEST_DUES_YEAR + 1
    template = request.registry.settings.get(
        'c3smembership.certificate_template', '')
    missing = []
    for kind in _TEMPLATE_KINDS:
        path = dues_year.latex_template(next_year, kind).format(template)
        if not os.path.isfile(path):
            missing.append(os.path.basename(path))

    return {
        'year': next_year,
        'templates_ready': len(missing) == 0,
        'missing_templates': missing,
        'template_dir': os.path.join('certificate', template),
    }


@view_config(renderer='c3smembership.presentation:templates/pages/dues.pt',
             permission='manage',
             route_name='dues')
def dues(request):
    """
    Show the dues page
    """
    status = next_year_status(request)
    return {
        'dues_years': sorted(DUES_YEARS, reverse=True),
        'latest_dues_year': LATEST_DUES_YEAR,
        'next_dues_year': status['year'] if status else None,
        'next_dues_year_templates_ready':
            status['templates_ready'] if status else False,
        'next_dues_year_missing': status['missing_templates'] if status else [],
        'next_dues_year_template_dir':
            status['template_dir'] if status else '',
    }
