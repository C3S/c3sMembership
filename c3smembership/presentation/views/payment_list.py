# -*- coding: utf-8 -*-
"""
Payment list view and payment content size provider for pagination.
"""


import datetime

import deform
from pyramid.view import view_config

from c3smembership.presentation.schemas.payment_list_filters import \
    create_payment_filter_form


FILTER_SETTINGS = {
    'from_date': {
        'type': 'date',
        'date_format': '%Y-%m-%d',
        'default': None,
    },
    'to_date': {
        'type': 'date',
        'date_format': '%Y-%m-%d',
        'default': None,
    },
}

FILTER_FORM = create_payment_filter_form()


def date_cookie_parser(cookie_value, filter_setting):
    """
    Parses a date from a cookie according to the filter cookie date format.

    Args:
        cookie_value: The string value of the cookie.
        filter_setting: The dictionary representing the filter cookie
            settings containing the date format as
            filter_setting['date_format'].

    Returns:
        The cookie value as a datetime.date object. If the cookie_value cannot
        be parsed according to the date format then the
        filter_setting['default'] is returned. If the default is not set then
        None is returned.

    Example:
        >>> cookie_value = '2018-06-14'
        >>> filter_setting = {
        >>>     'date_format': '%Y-%m-%d'
        >>> }
        >>> filter_value = date_cookie_parser(cookie_value, filter_setting)
        >>> filter_value
        datetime.date(2018, 6, 14)
    """
    filter_value = None
    try:
        filter_value = datetime.datetime.strptime(
            cookie_value,
            filter_setting['date_format']
        ).date()
    except ValueError:
        if 'default' in filter_setting:
            filter_value = filter_setting['default']
    return filter_value


COOKIE_PARSERS = {
    'date': date_cookie_parser
}


def date_cookie_formatter(filter_value, filter_setting):
    """
    Formats a date value as a string according to the date format specified
    in the filter setting.

    Args:
        filter_value: The date filter value to be formatted.
        filter_setting: The dictionary representing the filter cookie
            settings containing the date format as
            filter_setting['date_format'].

    Returns:
        The filter value as a string.

    Example:
        >>> filter_setting = {
        >>>     'date_format': '%Y-%m-%d'
        >>> }
        >>> filter_value = datetime.date(2018, 6, 14)
        >>> cookie_value = date_cookie_formatter(filter_value, filter_setting)
        >>> cookie_value
        '2018-06-14'
    """
    result = None
    if filter_value is not None:
        try:
            result = filter_value.strftime(filter_setting['date_format'])
        except TypeError:
            result = None
    return result


COOKIE_FORMATTERS = {
    'date': date_cookie_formatter
}


def get_filter_from_cookies(
        request, filtering, filter_settings, cookie_parsers):
    """
    Gets the filter settings from the request cookies and sets them to the
    provided filtering returning the filtering.

    Args:
        request: The pyramid.request.Request containing the cookies.
        filtering: A dictionary representing the filtering to which the cookie
            filter information is set.
        filter_settings: A dictionary representing the filter settings per name
            specifying the type.
        cookie_parsers: A dictionary representing the cookie parsers per type.

    Returns:
        A dictionary representing the filtering containing the filter
        information from the cookies.
    """
    for filter_name in filter_settings:
        cookie_name = u'payment_list.{}'.format(unicode(filter_name))
        if cookie_name in request.cookies:
            cookie_value = request.cookies[cookie_name]
            cookie_type = filter_settings[filter_name]['type']
            cookie_parser = cookie_parsers[cookie_type]
            filtering[filter_name] = cookie_parser(
                cookie_value,
                filter_settings[filter_name]
            )
    return filtering


def reset_filtering(filtering, filter_settings):
    """
    Resets the filter information in the filtering.

    All filters are set to their default value. If filters are not yet present
    in filtering they are created.

    Args:
        filtering: A dictionary representing the filtering for which the filter
            information is reset.
        filter_settings: A dictionary representing the filter settings
            providing the default for the filter name.

    Returns:
        A dictionary representing the filtering with filter information reset.
    """
    for filter_name in filter_settings:
        filtering[filter_name] = filter_settings[filter_name]['default']
    return filtering


def set_filters_to_cookies(
        request, filtering, filter_settings, cookie_formatters):
    """
    Sets the filter informtion to cookies.

    Args:
        request: The pyramid.request.Request to which on which the cookies are
            set with the filter information
        filtering: A dictionary representing the filtering containing the
            filter information.
        filter_settings: A dictionary representing the filter settings.
        cookie_formatters: A dictionary prodiving a cookie formatter per cookie
            name.
    """
    for filter_name in filter_settings:
        cookie_name = u'payment_list.{}'.format(unicode(filter_name))
        cookie_type = filter_settings[filter_name]['type']
        cookie_formatter = cookie_formatters[cookie_type]
        filter_value = filtering[filter_name]
        cookie_value = cookie_formatter(
            filter_value,
            filter_settings[filter_name])
        request.response.set_cookie(
            cookie_name,
            value=cookie_value)


def get_filtering(request, filter_settings, cookie_parsers):
    """
    Gets the filter information filtering from the request. First, defaults
    are set and then filter information is retrieved from cookies if available.

    Args:
        request: The pyramid.request.Request from which cookies are read.
        filter_settings: A dictionary representing the filter settings.
        cookie_parsers: A dictionary providing a cookie parser per type.

    Returns:
        A dictionary representing the filtering containing the filter
        information.
    """
    filtering = reset_filtering({}, filter_settings)
    filtering = get_filter_from_cookies(
        request, filtering, filter_settings, cookie_parsers)
    return filtering


def handle_filtering(
        request, filter_form, filter_settings, cookie_formatters,
        cookie_parsers):
    """
    Handles the filtering and the filter form.

    Args:
        request: The pyramid.request.Request object from which cookies and form
            data is retrieved.
        filter_form: The form which is validated for filter settings.
        filter_settings: A dictionary providing the filter settings.
        cookie_formatters: A dictionary providing cookie formatters per type.
        cookie_parsers: A dictionary providing cookie parsers per type.

    Returns:
        filter_form: The deform.Form object showing the filters.
        filtering: A dictionary containing the filter values.
    """
    filtering = get_filtering(request, filter_settings, cookie_parsers)
    if 'submit' not in request.POST and 'reset' not in request.POST:
        filter_form = filter_form.render(filtering)
    elif 'reset' in request.POST:
        filtering = reset_filtering(filtering, filter_settings)
        set_filters_to_cookies(
            request, filtering, filter_settings, cookie_formatters)
        filter_form = filter_form.render(filtering)
    elif 'submit' in request.POST:
        controls = request.POST.items()
        try:
            filtering = filter_form.validate(controls)
            filter_form = filter_form.render(filtering)
            set_filters_to_cookies(
                request, filtering, filter_settings, cookie_formatters)
        except deform.ValidationFailure as validation_failure:
            filter_form = validation_failure.render()
    return (filter_form, filtering)


@view_config(
    renderer='c3smembership.presentation:templates/pages/payment_list.pt',
    permission='manage',
    route_name='payment_list')
def payment_list(request):
    """
    Provides the payments according to sorting and filtering as well as a form
    for setting filters.

    Args:
        request: The pyramid.request.Request object from which form data and
            cookies are read.

    Returns:
        A dictionary containing the list of payments as well as the rendered
        filter form.
    """
    filter_form, filtering = handle_filtering(
        request,
        FILTER_FORM,
        FILTER_SETTINGS,
        COOKIE_FORMATTERS,
        COOKIE_PARSERS,
    )

    payments = request.registry.payment_information.get_payments(
        request.pagination.paging.page_number,
        request.pagination.paging.page_size,
        request.pagination.sorting.sort_property,
        request.pagination.sorting.sort_direction,
        filtering['from_date'],
        filtering['to_date'],
    )
    return {
        'payments': payments,
        'filter_form': filter_form
    }


def payment_content_size_provider(request):
    """
    Provides the payment content size, i.e. the number of payments available
    to be displayed.

    Args:
        request: The pyramid.request.Request object from which form data and
            cookie information is retrieved.

    Returns:
        An integer representing the number of payments available for the
        current filters.
    """
    filtering = handle_filtering(
        request,
        FILTER_FORM,
        FILTER_SETTINGS,
        COOKIE_FORMATTERS,
        COOKIE_PARSERS,
    )[1]
    return request.registry.payment_information.get_payment_count(
        filtering['from_date'],
        filtering['to_date'])
