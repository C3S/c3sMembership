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
from c3smembership.models import (
    C3sMember,
)
from c3smembership.tex_tools import TexTools


DEBUG = False


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_member_grant.pt',
    permission='manage',
    route_name='make_member')
def make_member_view(request):
    """
    Turns a membership applicant into an accepted member.

    When both the signature and the payment for the shares have arrived at
    headquarters, an application for membership can be turned into an
    **accepted membership**, if the board of directors decides so.

    This view lets staff enter a date of approval through a form.

    It also provides staff with listings of

    * members with same first name
    * members with same last name
    * members with same email address
    * members with same date of birth

    so staff can decide if this may become a proper membership
    or whether this application is a duplicate of some accepted membership
    and should be merged with some other entry.

    In case of duplicate/merge, also check if the number of shares
    when combining both entries would exceed 60,
    the maximum number of shares a member can hold.
    """
    afm_id = request.matchdict['afm_id']
    try:  # does that id make sense? member exists?
        member = C3sMember.get_by_id(afm_id)
        assert(isinstance(member, C3sMember))  # is an application
        # assert(isinstance(member.membership_number, NoneType)
        # not has number
    except AssertionError:
        return HTTPFound(
            location=request.route_url('dashboard'))
    if member.membership_accepted:
        # request.session.flash('id {} is already accepted member!')
        return HTTPFound(request.route_url('detail', memberid=member.id))

    if not (member.signature_received and member.payment_received):
        request.session.flash('signature or payment missing!', 'messages')
        return HTTPFound(request.route_url('dashboard'))

    if 'make_member' in request.POST:
        # print "yes! contents: {}".format(request.POST['make_member'])
        try:
            member.membership_date = datetime.strptime(
                request.POST['membership_date'], '%Y-%m-%d').date()
        except ValueError, value_error:
            request.session.flash(value_error.message, 'merge_message')
            return HTTPFound(
                request.route_url('make_member', afm_id=member.id))

        member.membership_accepted = True
        if member.is_legalentity:
            member.membership_type = u'investing'
        else:
            member.is_legalentity = False
        member.membership_number = C3sMember.get_next_free_membership_number()

        # Currently, the inconsistent data model stores the amount of applied
        # shares in member.num_shares which must be moved to a membership
        # application process property. As the acquisition of shares increases
        # the amount of shares and this is still read from member.num_shares,
        # this value must first be reset to 0 so that it can be increased by
        # the share acquisition. Once the new data model is complete the
        # property num_shares will not exist anymore. Instead, a membership
        # application process stores the number of applied shares and the
        # shares store the number of actual shares.
        num_shares = member.num_shares
        member.num_shares = 0

        share_id = request.registry.share_acquisition.create(
            member.membership_number,
            num_shares,
            member.membership_date)
        share_acquisition = request.registry.share_acquisition
        share_acquisition.set_signature_reception(
            share_id,
            date(
                member.signature_received_date.year,
                member.signature_received_date.month,
                member.signature_received_date.day))
        share_acquisition.set_payment_confirmation(
            share_id,
            date(
                member.payment_received_date.year,
                member.payment_received_date.month,
                member.payment_received_date.day))
        share_acquisition.set_reference_code(
            share_id,
            member.email_confirm_code)

        # return the user to the page she came from
        if 'referrer' in request.POST:
            if request.POST['referrer'] == 'dashboard':
                return HTTPFound(request.route_url('dashboard'))
            if request.POST['referrer'] == 'detail':
                return HTTPFound(
                    request.route_url('detail', memberid=member.id))
        return HTTPFound(request.route_url('detail', memberid=member.id))

    referrer = ''
    if 'dashboard' in request.referrer:
        referrer = 'dashboard'
    if 'detail' in request.referrer:
        referrer = 'detail'
    return {
        'member': member,
        'next_mship_number': C3sMember.get_next_free_membership_number(),
        'same_mships_firstn': C3sMember.get_same_firstnames(member.firstname),
        'same_mships_lastn': C3sMember.get_same_lastnames(member.lastname),
        'same_mships_email': C3sMember.get_same_email(member.email),
        'same_mships_dob': C3sMember.get_same_date_of_birth(
            member.date_of_birth),
        # keep information about the page the user came from in order to
        # return her to this page
        'referrer': referrer,
    }
