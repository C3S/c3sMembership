# -*- coding: utf-8 -*-
"""
Error handler for Colander validation
"""

from pyramid.httpexceptions import HTTPFound


class ErrorHandler(object):
    """
    Handle validation errors
    """
    # pylint: disable=too-few-public-methods

    def __call__(self, request, schema, errors):
        """
        Handle validation errors

        Args:
            request: The request of the action of which errors are handled
            schema: The Colander schema used to perform validation
            errors: The errors occurred during validation

        Returns:
            If other than None the value is passed to Pyramid instead of the
            view's result.
        """
        raise NotImplementedError()


class MultiErrorHandler(ErrorHandler):
    """
    Apply multiple validation error handlers
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, error_handlers):
        """
        Initialise the MultiErrorHandler object

        Args:
            error_handlers: an iterable of ErrorHandler objects
        """
        self._error_handlers = error_handlers

    def __call__(self, request, schema, errors):
        """
        Handle validation errors via the error handlers passed with
        initialisation

        Args:
            request: The request of the action of which errors are handled
            schema: The Colander schema used to perform validation
            errors: The errors occurred during validation

        Returns:
            If other than None the value is passed to Pyramid instead of the
            view's result.
        """
        for error_handler in self._error_handlers:
            result = error_handler(request, schema, errors)
            if result is not None:
                return result


class FlashCallbackErrorHandler(MultiErrorHandler):
    """
    Handle errors by flashing them to request.session and performing a callback
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, redirect_callback):
        """
        Initialise the FlashCallbackErrorHandler object

        Args:
            redirect_callback: An object implementing the ErrorHandler
                interface which is called after flashing the errors to
                request.session.
        """
        super(FlashCallbackErrorHandler, self).__init__(
            [
                self._flash,
                redirect_callback,
            ])

    @classmethod
    def _flash(cls, request, schema, errors):
        """
        Flash the errors to to request.session

        Args:
            request: The request of the action of which errors are handled
            schema: The Colander schema used to perform validation
            errors: The errors occurred during validation
        """
        # pylint: disable=unused-argument
        for node_name in errors:
            request.session.flash(
                errors[node_name],
                'danger')


class FlashErrorHandler(FlashCallbackErrorHandler):
    """
    Handle errors by flashing them to request.session and forwarding to a
    specified route

    The route can either be specified with object intialisation or via the
    optional schema.error_route attribute.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, error_route=None):
        """
        Initialise the FlashErrorHandler object

        Args:
            error_route: Optional. The error route to which to be forwarded
            after flashing the errors to request.session
        """
        super(FlashErrorHandler, self).__init__(
            self._error_route_redirect)
        self._error_route = error_route

    def _error_route_redirect(self, request, schema, errors):
        """
        Redirect to error_route if specified

        The redirect is performed to this object's error route if specified
        during initialisation or schema.error_route if available.

        Args:
            request: The request of the action of which errors are handled
            schema: The Colander schema used to perform validation
            errors: The errors occurred during validation
        """
        # pylint: disable=unused-argument
        error_route = None
        if self._error_route is not None:
            error_route = self._error_route
        elif hasattr(schema, 'error_route'):
            error_route = schema.error_route
        if error_route is not None:
            return HTTPFound(request.route_url(error_route))
