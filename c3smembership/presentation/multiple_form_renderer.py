# -*- coding: utf-8 -*-
"""
Provides functionality to handle multiple forms on the same view.
"""

from deform import ValidationFailure


class IFormValidationEvent(object):
    # pylint: disable=too-few-public-methods
    """
    Specifies the interface of a python callable for successful form
    validations.

    A common usage of this callback is to perform a redirect using an HTTPFound
    Pyramid exception based on the form's data.

    Example:

        class SomeRouteRedirect(IFormValidationEvent):
            def __call__(self, request, result, appstruct):
                return HTTPFound(
                    location=request.route_url(
                        'some_route',
                        date=appstruct['date']))

    Example:

        def some_route_redirect(request, result, appstruct):
            return HTTPFound(
                location=request.route_url(
                    'some_route',
                    date=appstruct['date']))
    """

    def __call__(self, request, result, appstruct):
        """
        Handles the submitted form data after a successful form validation.

        Args:
            request: The Pyramid request which submitted the form.
            result: The view's result to which the form is rendered.
            appstruct: The data submitted to the form.

        Returns:
            Any data which can be returned to the view of which the forms are
            rendered.

            This can be a redirect using an HTTPFound Pyramid exception of a
            modified result dictionary which possibly among other data contains
            the rendered forms.
        """
        raise NotImplementedError()


class MultipleFormRenderer(object):
    """
    MultipleFormRenderer enables rendering, validation and callbacks of
    multiple forms.

    All forms added to the MultipleFormRenderer are rendered to the result. In
    case the form was submitted the form is validated. Callbacks for
    """

    def __init__(self):
        """
        Initialises the MultipleFormRenderer.
        """
        self.__forms = {}
        self.__validation_success = {}
        self.__validation_failure = {}

    def add_form(self, form, validation_success=None, validation_failure=None):
        """
        Adds a form to the renderer which will be rendered and validated.

        Args:
            form: The form to be added to the renderer.
            validation_success: A python callable which is called in case
                the form was successfully validated. The result of this
                callable is returned to the view.
            validation_failure: A python callable which is called in case
                the form validation failed. The result of this callable is
                returned to the view.
        """
        self.__forms[form.formid] = form
        if validation_success is not None:
            self.__validation_success[form.formid] = \
                validation_success
        if validation_failure is not None:
            self.__validation_failure[form.formid] = \
                validation_failure

    def render(self, request, result):
        """
        Renders the forms, validates the form which was submitted and performs
        callbacks if available.

        Args:
            request: The Pyramid request.
            result: The view's result to which the forms are rendered.
        """
        result = dict(result)
        # render forms to result
        for formid in self.__forms:
            result[formid] = self.__forms[formid].render()

        # handle posted form
        if request.method == 'POST':
            post_formid = request.POST['__formid__']
            if post_formid in self.__forms:
                form = self.__forms[post_formid]
                try:
                    # validate the form
                    appstruct = form.validate(request.POST.items())
                    # perform callback if available and return result
                    if post_formid in self.__validation_success:
                        callback = self.__validation_success[post_formid]
                        return callback(request, result, appstruct)
                except ValidationFailure as validation_failure:
                    # in case of a validation failure, replace the
                    # originally rendered form with the validation result
                    result[form.formid] = validation_failure.render()
                    # perform callback if available and return result
                    if post_formid in self.__validation_failure:
                        callback = self.__validation_failure[post_formid]
                        return callback(
                            request,
                            result,
                            validation_failure.cstruct)
        return result
