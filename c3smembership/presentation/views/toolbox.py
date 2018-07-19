# -*- coding: utf-8 -*-

from datetime import date

import deform
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.presentation.i18n import _
from c3smembership.presentation.multiple_form_renderer import (
    MultipleFormRenderer
)
from c3smembership.presentation.schemas.membership_listing import (
    MembershipListingDate,
    MembershipListingYearEnd,
)


def membership_listing_date_pdf_callback(request, result, appstruct):
    """
    Forwards to the membership listing pdf route for the given date.
    """
    return HTTPFound(
        location=request.route_url(
            'membership_listing_date_pdf',
            date=appstruct['date']))


def build_form_renderer():
    """
    Builds the form handler by creating and adding the forms.
    """

    # build forms
    membership_listing_date_pdf_form = deform.Form(
        MembershipListingDate(),
        buttons=[deform.Button('submit', _(u'Generate PDF'))],
        formid='membership_listing_date_pdf')

    membership_listing_year_end_pdf_form = deform.Form(
        MembershipListingYearEnd(),
        buttons=[deform.Button('submit', _(u'Generate PDF'))],
        formid='membership_listing_year_end_pdf'
    )

    # create form handler
    form_renderer = MultipleFormRenderer()

    # add forms
    form_renderer.add_form(
        membership_listing_date_pdf_form,
        membership_listing_date_pdf_callback)
    form_renderer.add_form(
        membership_listing_year_end_pdf_form,
        membership_listing_date_pdf_callback)
    return form_renderer


@view_config(
    renderer='c3smembership.presentation:templates/pages/membership_tools.pt',
    permission='manage',
    route_name='toolbox')
def toolbox(request):
    """
    Toolbox: This view shows many options.

    The view is rather minimal, but the template has all the links:

    - Statistics and Reporting
       - Statistics
       - Annual Reporting
       - Postal Codes (TODO)
    - Search
       - Search for Codes
       - Search for People
    - Applications for Membership
       - AfM dashboard
       - AfMs ready for approval by the board
    - Members List (HTML)
       - with links -- useful for interaction (like the dashboard)
       - without links -- useful for printout
       - Alphabetical Aufstockers List
    - Members List (PDF)
    - Import & Export
    - ...
    """

    form_renderer = build_form_renderer()
    result = {
        'date': date.today().strftime('%Y-%m-%d')
    }
    result = form_renderer.render(request, result)
    return result
