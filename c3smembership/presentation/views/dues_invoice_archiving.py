# -*- coding: utf-8 -*-
"""
Offers functionality to archive invoices
"""

import logging
from threading import Thread

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.presentation.schemas.dues import create_archiving_form
from c3smembership.presentation.multiple_form_renderer import \
    MultipleFormRenderer


LOGGER = logging.getLogger(__name__)


class AlreadyRunningError(Exception):
    """
    Raised when background archiving is already running
    """
    pass


class AlreadyStoppedError(Exception):
    """
    Raised when background archiving is already stopped
    """
    pass


class BackgroundArchivingControl(object):
    """
    Control for background archiving

    The control is used as a singleton to control the background archiving as
    well as provide information about the running process.
    """

    _error = False
    _running = False
    _count = 0
    _total = 0

    @classmethod
    def is_running(cls):
        """
        Indicate whether the background archiving process is currently running
        """
        return cls._running

    @classmethod
    def start(cls, total):
        """
        Start the background archiving process

        Args:
            total: Integer. The total number of invoices which are archived in
                background

        Raises:
            AlreadyRunningError: In case background archiving is already
                running.
        """
        if cls._running:
            raise AlreadyRunningError()
        cls._error = False
        cls._running = True
        cls._count = 0
        cls._total = total

    @classmethod
    def get_total(cls):
        """
        Get the total number of invoices which are archived in background
        """
        return cls._total

    @classmethod
    def increment_count(cls):
        """
        Increment the invoice count archived in bakcground
        """
        cls._count += 1

    @classmethod
    def get_count(cls):
        """
        Get the count of invoices archived in background
        """
        return cls._count

    @classmethod
    def stop(cls):
        """
        Stop background archiving

        Raises:
            AlreadyStoppedError: In case background archiving is already
                stopped.
        """
        if not cls.is_running():
            raise AlreadyStoppedError()
        cls._running = False

    @classmethod
    def set_error(cls):
        """
        Set an error state for background archiving
        """
        cls._error = True

    @classmethod
    def has_error(cls):
        """
        Get the error state for background archiving
        """
        return cls._error


@view_config(
    permission='manage',
    route_name='batch_archive_pdf_invoices',
    renderer='c3smembership:presentation/templates/pages/invoice_archiving.pt')
def batch_archive_pdf_invoices(request):
    """
    Generate and archive a number of invoices

    Note:
        Expects the object request.registry.dues_invoice_archiving to implement
        c3smembership.business.dues_invoice_archiving.DuesInvoiceArchiving.
    """
    form_renderer = build_form_renderer(request)
    archiving_stats = get_archiving_stats(request)
    archiving_stats_sums = get_archiving_stats_sums(archiving_stats)

    result = {
        'generated_invoices': [],
        'archiving_stats': archiving_stats,
        'archiving_stats_sums': archiving_stats_sums,
        'background_archiving_active': BackgroundArchivingControl.is_running(),
        'background_archiving_count': BackgroundArchivingControl.get_count(),
        'background_archiving_total': BackgroundArchivingControl.get_total(),
        'background_archiving_error': BackgroundArchivingControl.has_error(),
    }
    return form_renderer.render(request, result)


@view_config(
    permission='manage',
    route_name='background_archive_pdf_invoices')
def background_archive_pdf_invoices(request):
    """
    Start background invoice archiving

    Only start background archiving if not already in progress.
    """
    # For dependency injection purposes
    background_archiving_control = \
        background_archive_pdf_invoices.background_archiving_control
    logger = background_archive_pdf_invoices.logger

    if not background_archiving_control.is_running():
        background_archiving_control.start(get_not_archived_sum(request))
        logger.info('Starting background invoice archiving')
        thread = Thread(
            target=background_archiving,
            args=(
                request.registry.dues_invoice_archiving,
                background_archiving_control,))
        thread.start()
    else:
        logger.info('Invoice archiving already running')
    return HTTPFound(request.route_url('batch_archive_pdf_invoices'))

background_archive_pdf_invoices.background_archiving_control = \
    BackgroundArchivingControl
background_archive_pdf_invoices.logger = LOGGER


def get_archiving_stats_sums(stats):
    """
    Get the sums of the statistics

    The sums of the statistics are calculated in order to show a total row at
    the bottom of the table.
    """
    archiving_stats_sums = {}
    archiving_stats_sums['year'] = len(stats)
    archiving_stats_sums['total'] = 0
    archiving_stats_sums['archived'] = 0
    archiving_stats_sums['not_archived'] = 0
    for stat in stats:
        archiving_stats_sums['total'] += stat['total']
        archiving_stats_sums['archived'] += stat['archived']
        archiving_stats_sums['not_archived'] += stat['not_archived']
    return archiving_stats_sums


def get_archiving_stats(request):
    """
    Get statistics about archiving status for all years
    """
    return request.registry.dues_invoice_archiving.get_archiving_stats()


def build_form_renderer(request):
    """
    Build the form renderer for the dues invoice archiving form
    """
    form_renderer = MultipleFormRenderer()
    form = create_archiving_form(request)
    form.formid = 'form'
    form_renderer.add_form(form, archive_invoices)
    return form_renderer


def archive_invoices(request, result, appstruct):
    """
    Archive the invoices
    """
    dues_invoice_archiving = request.registry.dues_invoice_archiving
    result['generated_invoices'] = dues_invoice_archiving \
        .generate_missing_invoice_pdfs(
            appstruct['archive_invoices']['year'],
            appstruct['archive_invoices']['count'])
    flash_message(
        request,
        result['generated_invoices'],
        appstruct['archive_invoices']['count'])

    # refresh as the initial set is not up-to-date anymore
    result['archiving_stats'] = get_archiving_stats(request)

    return result


def get_not_archived_sum(request):
    """
    Get the total number of invoices not archived yet for all years
    """
    stats_sums = get_archiving_stats_sums(get_archiving_stats(request))
    return stats_sums['not_archived']


def flash_message(request, generated_invoices, count):
    """
    Construct the message for invoice archiving to be displayed
    """
    if generated_invoices is not None:
        queue = 'success'
        if generated_invoices:
            message = 'Successfully archived {0} invoices.'.format(
                len(generated_invoices))
            if len(generated_invoices) == count:
                message += ' There might be more invoices to be archived.'
            else:
                message += ' There are no more invoices to be ' + \
                    'archived at the moment.'
        else:
            message = 'There were no invoices to be archived.'
    else:
        message = 'An error occurred during archiving the invoices.'
        queue = 'danger'
    request.session.flash(message, queue)


def background_archiving(dues_invoice_archiving, background_archiving_control):
    """
    Archive all remaining invoices in background
    """
    # All exceptions have to be collected and written to the log.
    # pylint: disable=bare-except
    logger = background_archiving.logger
    try:
        stats = dues_invoice_archiving.get_archiving_stats()
        for stat in stats:
            generated_invoices = []
            while True:
                generated_invoices = dues_invoice_archiving \
                    .generate_missing_invoice_pdfs(stat['year'], 1)
                if len(generated_invoices) == 1:
                    logger.info(
                        'Generated %d invoice: %s',
                        len(generated_invoices),
                        str(generated_invoices[0]))
                    background_archiving_control.increment_count()
                else:
                    break
        logger.info('Finished background invoice archiving')
    except:
        logger.exception(
            'An error occured during background invoice archiving')
        background_archiving_control.set_error()
    background_archiving_control.stop()

background_archiving.logger = LOGGER
