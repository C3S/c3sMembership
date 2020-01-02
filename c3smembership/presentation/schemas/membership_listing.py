# -*- coding: utf-8 -*-
"""
Form and validation schemas for membership listings.
"""

import datetime

import colander
import deform

from c3smembership.presentation.i18n import _


@colander.deferred
def deferred_date_validator(node, keywords):
    """
    The deferred listing by date validator

    The maximum date is the date of the submitting of the form.

    As the maximum date must be set during execution runtime and not during
    schema declaration, this validator is implemented as deferred.
    """
    return colander.Range(
            max=datetime.date.today(),
            max_err=_('${val} is later than today'))


@colander.deferred
def deferred_date_default(node, keywords):
    """
    The deferred listing default date

    The default date is the date of the rendering of the form.

    As the default date must be set during execution runtime and not during
    schema declaration, this it is implemented as deferred.
    """
    return datetime.date(2019, 12, 31)


@colander.deferred
def deferred_year_end_select_widget(node, keywords):
    """
    The deferred select widget for the year end form

    The select widget contains all year numbers from 2013 to the date of the
    form rendering.

    As the years must be calculated during execution runtime and not during
    schema declaration, the widget is implemented as deferred.

    TODO: 2013 as the first year for which to create a membership list should
    be dynamically determined using the minimum membership date.
    """
    return deform.widget.SelectWidget(
        values=[(datetime.date(year, 12, 31), str(year))
                for year in reversed(range(2013,
                                           datetime.date.today().year))])


class MembershipListingDate(colander.Schema):
    """
    Provides a colander schema for entering a date.
    """
    date = colander.SchemaNode(
        colander.Date(),
        title=_('Date'),
        validator=deferred_date_validator,
        default=deferred_date_default)


class MembershipListingYearEnd(colander.Schema):
    """
    Provides a colander schema for selecting a year.
    """

    date = colander.SchemaNode(
        colander.Date(),
        title=_('Year'),
        widget=deferred_year_end_select_widget,
    )
