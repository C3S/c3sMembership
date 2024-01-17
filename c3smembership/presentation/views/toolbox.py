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
from c3smembership.presentation.schemas.mass_payment_confirmation import (
    MassPaymentConfirmation
)

from c3smembership.presentation.schemas.invoice_search import (
    InvoiceSearch
)

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember

def membership_listing_date_pdf_callback(request, result, appstruct):
    """
    Forwards to the membership listing pdf route for the given date.
    """
    return HTTPFound(
        location=request.route_url(
            'membership_listing_date_pdf',
            date=appstruct['date']))


def mass_payment_confirmation_callback(request, result, appstruct):
    """
    Forwards to the mass payment confirmation route for the given codes.
    """
    return HTTPFound(
        location=request.route_url(
            'mass_payment_confirmation',
            text=appstruct['text']))


def invoice_search_callback(request, result, appstruct):
    """
    Forwards to the dues tab of a member, containing this invoice.
    """
    # import debugpy
    # debugpy.listen(("0.0.0.0", 5253))
    # print("Waiting for debugger attach")
    # debugpy.wait_for_client()
    # debugpy.breakpoint()

    invoicecode=appstruct['invoicecode']
    if len(invoicecode) == 17:
        invoicecode = invoicecode[8:]
    yy = invoicecode[2:4]
    db_dues_invoice_no = getattr(C3sMember, f"dues{yy}_invoice_no")
    members = DBSession().query(C3sMember).where(db_dues_invoice_no
        == int(invoicecode[5:]))
    if members.count() == 0:   # invoice code not found
        request.session.flash(
            f"Invoice number {invoicecode} not found. ",
            'danger'
        )
        return HTTPFound(request.route_url('error'))

    if members.count() > 1:  # obscure case
        request.session.flash(
            f"Invoice number {invoicecode} found for more than one "
            "member. This shouldn't occur. Please check db integrity!",
            'danger'
        )
        return HTTPFound(request.route_url('error'))
    member = members.one()

    return HTTPFound(
        location=request.route_url('detail', member_id=member.id) + "#dues")

def build_form_renderer():
    """
    Builds the form handler by creating and adding the forms.
    """

    # build forms
    membership_listing_date_pdf_form = deform.Form(
        MembershipListingDate().bind(),
        buttons=[deform.Button('submit', _('Generate PDF'))],
        formid='membership_listing_date_pdf')

    membership_listing_year_end_pdf_form = deform.Form(
        MembershipListingYearEnd().bind(),
        buttons=[deform.Button('submit', _('Generate PDF'))],
        formid='membership_listing_year_end_pdf'
    )

    mass_payment_confirmation_form = deform.Form(
        MassPaymentConfirmation().bind(),
        buttons=[deform.Button('submit', _('Confirm Payments'))],
        formid='mass_payment_confirmation_form'
    )

    invoice_search_form = deform.Form(
        InvoiceSearch().bind(),
        buttons=[deform.Button('submit', _('Search'))],
        formid='invoice_search_form'
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
    form_renderer.add_form(
        mass_payment_confirmation_form,
        mass_payment_confirmation_callback)
    form_renderer.add_form(
        invoice_search_form,
        invoice_search_callback)
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
    - Mass Payment Confirmation (processes CSV input from Hibiscus banking)
    - Import & Export
    - ...
    """

    form_renderer = build_form_renderer()
    result = {
        'date': date.today().strftime('%Y-%m-%d')
    }
    result = form_renderer.render(request, result)
    return result
