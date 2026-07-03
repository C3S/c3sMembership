# -*- coding: utf-8 -*-
"""
Form and validation schemas for the member list export.

The member list can be exported as a CSV file or shown as a printable HTML
list, e.g. for general assemblies and mailings. The schema provides:

- a selection of the personal data fields to be included
- an email exclusion pattern with "*" as wildcard
- filters for membership type, membership acceptance and membership loss
"""

import datetime

import colander
import deform

from c3smembership.presentation.i18n import (
    _,
    ZPT_RENDERER,
)


# Fields of the members table containing personal data which can be included
# in the export. The order of this list defines the column order of the
# output.
EXPORT_FIELDS = [
    ('membership_number', _('Membership number')),
    ('firstname', _('First name')),
    ('lastname', _('Last name')),
    ('email', _('Email address')),
    ('locale', _('Language')),
    ('address1', _('Address line 1')),
    ('address2', _('Address line 2')),
    ('postcode', _('Postal code')),
    ('city', _('City')),
    ('country', _('Country')),
    ('date_of_birth', _('Date of birth')),
    ('membership_type', _('Membership type')),
    ('membership_date', _('Membership date')),
    ('membership_loss_date', _('Membership loss date')),
    ('num_shares', _('Number of shares')),
]

DEFAULT_EXPORT_FIELDS = ['firstname', 'lastname', 'email', 'locale']

MEMBERSHIP_TYPE_ALL = 'all'

MEMBERSHIP_TYPE_OPTIONS = [
    ('normal', _('normal')),
    ('investing', _('investing')),
    (MEMBERSHIP_TYPE_ALL, _('all')),
]

# Maps the membership status form value to the membership_accepted filter
# value of the member repository.
MEMBERSHIP_STATUS_FILTERS = {
    'accepted': True,
    'not_accepted': False,
    'all': None,
}

MEMBERSHIP_STATUS_OPTIONS = [
    ('accepted', _('accepted (membership_accepted is true)')),
    ('not_accepted', _('not accepted (membership_accepted is false)')),
    ('all', _('all')),
]


@colander.deferred
def deferred_loss_date_default(node, keywords):
    """
    The deferred membership loss cut-off default date

    The default date is the system date of the rendering of the form.

    As the default date must be set during execution runtime and not during
    schema declaration, it is implemented as deferred.
    """
    # pylint: disable=unused-argument
    return datetime.date.today()


@colander.deferred
def deferred_email_exclude_default(node, keywords):
    """
    The deferred email exclusion pattern default

    The default differs between the CSV export ("*.invalid") and the print
    list ("") and is therefore passed as binding keyword
    email_exclude_default.
    """
    # pylint: disable=unused-argument
    return keywords.get('email_exclude_default', '')


class MemberListExport(colander.Schema):
    """
    Provides a colander schema for the member list export form.
    """
    fields = colander.SchemaNode(
        colander.Set(),
        title=_('Fields'),
        description=_('The fields to be included in the output.'),
        widget=deform.widget.CheckboxChoiceWidget(values=EXPORT_FIELDS),
        validator=colander.Length(
            min=1,
            min_err=_('Select at least one field.')),
        default=DEFAULT_EXPORT_FIELDS)
    email_exclude = colander.SchemaNode(
        colander.String(),
        title=_('Exclude email addresses'),
        description=_(
            'Members with an email address matching this pattern are '
            'excluded from the output. The asterisk "*" matches any '
            'number of characters, e.g. "*.invalid" excludes placeholder '
            'addresses. Leave empty to not exclude any member.'),
        default=deferred_email_exclude_default,
        missing='')
    membership_type = colander.SchemaNode(
        colander.String(),
        title=_('Membership type'),
        widget=deform.widget.SelectWidget(values=MEMBERSHIP_TYPE_OPTIONS),
        validator=colander.OneOf(
            [option[0] for option in MEMBERSHIP_TYPE_OPTIONS]),
        default=MEMBERSHIP_TYPE_ALL)
    membership_status = colander.SchemaNode(
        colander.String(),
        title=_('Membership status'),
        widget=deform.widget.SelectWidget(values=MEMBERSHIP_STATUS_OPTIONS),
        validator=colander.OneOf(
            [option[0] for option in MEMBERSHIP_STATUS_OPTIONS]),
        default='accepted')
    membership_loss_date = colander.SchemaNode(
        colander.Date(),
        title=_('Membership loss before'),
        description=_(
            'Members whose membership loss date lies before this date are '
            'excluded from the output. It defaults to today so that '
            'members whose resignation only becomes effective in the '
            'future are still included.'),
        default=deferred_loss_date_default)


class MemberListExportFormFactory(object):
    """
    Factory creating member list export Deform forms
    """
    # pylint: disable=too-few-public-methods

    @classmethod
    def create(cls, email_exclude_default, button_title):
        """
        Create a member list export form

        Args:
            email_exclude_default: String. The default value of the email
                exclusion pattern field, e.g. "*.invalid" for the CSV export
                and "" for the print list.
            button_title: String. The title of the submit button.
        """
        return deform.Form(
            MemberListExport().bind(
                email_exclude_default=email_exclude_default),
            buttons=[deform.Button('submit', button_title)],
            renderer=ZPT_RENDERER)
