# -*- coding: utf-8 -*-
"""
Merge members
"""
from datetime import (
    date,
    datetime,
)

import os
import shutil
import subprocess
import tempfile

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.tex_tools import TexTools


DEBUG = False


@view_config(permission='manage',
             route_name='merge_member')
def merge_member_view(request):
    """
    Merges member duplicates into one member record.

    Some people have more than one entry in our C3SMember table,
    e.g. because they used the application form more than once
    to acquire more shares.

    They shall not, however, become members twice and get more than one
    membership number. So we try and merge them:

    If a person is already a member and acquires a second package of shares,
    this package of shares is added to the former membership entry.
    The second entry in the C3sMember table is given the 'is_duplicate' flag
    and also the 'duplicate_of' is given the *id* of the original entry.
    """
    afm_id = request.matchdict['afm_id']
    member_id = request.matchdict['mid']
    if DEBUG:  # pragma: no cover
        print("shall merge {} to {}".format(afm_id, member_id))

    orig = C3sMember.get_by_id(member_id)
    merg = C3sMember.get_by_id(afm_id)

    if not orig.membership_accepted:
        request.session.flash(
            'you can only merge to accepted members!',
            'danger')
        HTTPFound(request.route_url('make_member', afm_id=afm_id))
    exceeds_60 = int(orig.num_shares) + int(merg.num_shares) > 60
    if exceeds_60:
        request.session.flash(
            'merger would exceed 60 shares!',
            'danger')
        return HTTPFound(request.route_url('make_member', afm_id=afm_id))

    # TODO: this needs fixing!!!
    # date must be set manually according to date of approval of the board
    shares_date_of_acquisition = merg.signature_received_date if (
        merg.signature_received_date > merg.payment_received_date
    ) else merg.payment_received_date

    share_acquisition = request.registry.share_acquisition
    share_id = share_acquisition.create(
        orig.membership_number,
        merg.num_shares,
        shares_date_of_acquisition)
    share_acquisition.set_signature_reception(
        share_id,
        date(
            merg.signature_received_date.year,
            merg.signature_received_date.month,
            merg.signature_received_date.day))
    share_acquisition.set_signature_confirmation(
        share_id,
        date(
            merg.signature_confirmed_date.year,
            merg.signature_confirmed_date.month,
            merg.signature_confirmed_date.day))
    share_acquisition.set_payment_reception(
        share_id,
        date(
            merg.payment_received_date.year,
            merg.payment_received_date.month,
            merg.payment_received_date.day))
    share_acquisition.set_payment_confirmation(
        share_id,
        date(
            merg.payment_confirmed_date.year,
            merg.payment_confirmed_date.month,
            merg.payment_confirmed_date.day))
    share_acquisition.set_reference_code(
        share_id,
        merg.email_confirm_code)

    DBSession.delete(merg)
    return HTTPFound(request.route_url('detail', member_id=member_id))
