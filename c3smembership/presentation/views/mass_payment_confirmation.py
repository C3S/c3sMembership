# -*- coding: utf-8 -*-
"""
This module holds functionality to handle the C3S SCEs membership list.

Having and maintaining an alphabetical membership list is one of the
obligations of an association like the C3S SCE.

The list is available in several formats:

- HTML with clickable links for browsing
- HTML without links for printout
- PDF (created with pdflatex) for printout (preferred!)

There are also some historic utility functions for reference:

- Turn founders into members
- Turn crowdfunders into members
- Turn form users into members
- Flag duplicates
- Merge duplicates
"""

import os
import shutil
import subprocess
import tempfile

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember

DEBUG = False


@view_config(permission='manage',
             route_name='mass_payment_confirmation')
def mass_payment_confirmation(request):
    """
    Process payments and show results.
    """

    import debugpy
    debugpy.listen(("0.0.0.0", 5253))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
    debugpy.breakpoint()
    print('break on this line')

    effective_date_string = ''
    try:
        text_string = request.matchdict['text']
    except (KeyError, ValueError):
        request.session.flash(
            "Invalid sequence of payment codes from banking references.",
            'danger'
        )
        return HTTPFound(request.route_url('error'))

    response = Response(content_type='text/plain ')
    return response
