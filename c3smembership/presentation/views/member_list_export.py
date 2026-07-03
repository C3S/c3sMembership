# -*- coding: utf-8 -*-
"""
Member list export for general assemblies and mailings.

The member list can be downloaded as a CSV file or shown as a printable HTML
list. The personal data fields to be included can be chosen and the list can
be filtered by membership type, membership acceptance and membership loss
date. Members whose email address matches a wildcard pattern can be excluded,
e.g. members with "*.invalid" placeholder addresses for a mailing.

A member whose membership loss date lies in the future, e.g. because the
resignation only becomes effective at the end of the year, is still a member
and therefore included until the membership loss cut-off date entered in the
form is greater than the membership loss date.

The CSV file is semicolon separated, all values quoted and UTF-8 encoded with
a byte order mark so that spreadsheet applications recognize the encoding.
The CSV header row contains the technical field names in order to be stable
for further processing like mail merge, independent of the user interface
language.
"""

import csv
from datetime import date
from fnmatch import fnmatchcase
import io

import deform
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.presentation.i18n import _
from c3smembership.presentation.schemas.member_list_export import (
    EXPORT_FIELDS,
    MEMBERSHIP_STATUS_FILTERS,
    MEMBERSHIP_TYPE_ALL,
    MemberListExportFormFactory,
)


CSV_EMAIL_EXCLUDE_DEFAULT = '*.invalid'


def get_filtered_members(request, appstruct):
    """
    Gets the members matching the filter criteria of the validated form.

    The members are filtered by membership type, membership acceptance and
    membership loss cut-off date. Members whose email address matches the
    email exclusion pattern are excluded. The email addresses are matched
    case-insensitively with "*" matching any number of characters.

    Args:
        request: The Pyramid request used to access the member information.
        appstruct: The validated appstruct of the member list export form.

    Returns:
        The members matching the filter criteria sorted by lastname ascending
        and firstname ascending.
    """
    membership_type = appstruct['membership_type']
    if membership_type == MEMBERSHIP_TYPE_ALL:
        membership_type = None
    members = request.registry.member_information.get_members_filtered(
        membership_type=membership_type,
        membership_accepted=MEMBERSHIP_STATUS_FILTERS[
            appstruct['membership_status']],
        membership_loss_threshold=appstruct['membership_loss_date'])
    pattern = appstruct['email_exclude'].strip().lower()
    if pattern:
        members = [
            member for member in members
            if not fnmatchcase((member.email or '').lower(), pattern)]
    return members


def get_export_columns(selected_fields):
    """
    Gets the columns for the selected fields.

    Args:
        selected_fields: The set of field names selected in the form.

    Returns:
        A list of (name, title) tuples in the order defined by EXPORT_FIELDS
        so that the column order is independent of the selection order.
    """
    return [
        column for column in EXPORT_FIELDS if column[0] in selected_fields]


def format_value(value):
    """
    Formats a member attribute value for output.

    None becomes an empty string, dates are formatted as YYYY-MM-DD and all
    other values are converted to strings.
    """
    if value is None:
        return ''
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    return str(value)


def get_member_rows(members, columns):
    """
    Gets the output rows for the members restricted to the columns.

    Args:
        members: The members for which rows are created.
        columns: A list of (name, title) tuples of the columns to be
            included.

    Returns:
        A list of lists of formatted values, one list per member.
    """
    return [
        [format_value(getattr(member, column[0])) for column in columns]
        for member in members]


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'member_list_export.pt',
    route_name='member_list_export_csv',
    permission='manage')
def member_list_export_csv(request):
    """
    Member list CSV export

    Shows the export form and returns the CSV file upon submission.
    """
    form = MemberListExportFormFactory.create(
        CSV_EMAIL_EXCLUDE_DEFAULT, _('Download CSV'))
    result = {
        'title': _('Member list CSV export'),
        'description': _(
            'Download the member list as a CSV file, e.g. for mailings. '
            'The file is semicolon separated and UTF-8 encoded.'),
    }
    if 'submit' in request.POST:
        try:
            appstruct = form.validate(list(request.POST.items()))
        except deform.ValidationFailure as validation_failure:
            result['form'] = validation_failure.render()
            return result
        members = get_filtered_members(request, appstruct)
        columns = get_export_columns(appstruct['fields'])
        csv_file = io.StringIO()
        writer = csv.writer(csv_file, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow([column[0] for column in columns])
        writer.writerows(get_member_rows(members, columns))
        return Response(
            # A byte order mark makes spreadsheet applications recognize
            # the UTF-8 encoding
            body='\ufeff' + csv_file.getvalue(),
            content_type='text/csv',
            charset='utf-8',
            content_disposition=(
                'attachment; filename="member_list_{}.csv"'.format(
                    date.today().strftime('%Y-%m-%d'))))
    result['form'] = form.render()
    return result


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'member_list_export.pt',
    route_name='member_list_export_print',
    permission='manage')
def member_list_export_print(request):
    """
    Printable member list

    Shows the export form and renders the member list as a printable HTML
    page upon submission. In contrast to the CSV export, no email addresses
    are excluded by default because for example an attendance list for a
    general assembly must contain all members.
    """
    form = MemberListExportFormFactory.create('', _('Show print list'))
    result = {
        'title': _('Member list for printout'),
        'description': _(
            'Show the member list as a printable HTML page, e.g. for '
            'general assemblies.'),
    }
    if 'submit' in request.POST:
        try:
            appstruct = form.validate(list(request.POST.items()))
        except deform.ValidationFailure as validation_failure:
            result['form'] = validation_failure.render()
            return result
        members = get_filtered_members(request, appstruct)
        columns = get_export_columns(appstruct['fields'])
        return render_to_response(
            'c3smembership.presentation:templates/pages/'
            'member_list_export_print.pt',
            {
                'column_titles': [column[1] for column in columns],
                'rows': get_member_rows(members, columns),
                'count': len(members),
                'membership_loss_date': appstruct['membership_loss_date'],
                'today': date.today(),
            },
            request=request)
    result['form'] = form.render()
    return result
