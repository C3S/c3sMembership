# -*- coding: utf-8 -*-
"""
Tests the c3smembership.presentation.multiple_form_renderer module.
"""

import unittest
import mock

from deform import ValidationFailure

from c3smembership.presentation import multiple_form_renderer
from c3smembership.presentation.multiple_form_renderer import (
    IFormValidationEvent,
    MultipleFormRenderer,
)


class MockValidationFailure(BaseException):
    """
    Mock for deform.ValidationFailure
    """

    def __init__(self, render_result=None, cstruct=None):
        """
        Initialises the MockValidationFailure object.

        Args:
            render_result: The optional value returned by the render method.
            cstruct: The optional cstruct returned by the cstruct property.
        """
        super(MockValidationFailure, self).__init__()
        self.__render_counter = 0
        self.__render_result = render_result
        self.__cstruct = cstruct

    def render(self):
        """
        Mocks the render method and increases the render counter.
        """
        self.__render_counter += 1
        return self.__render_result

    def get_render_counter(self):
        """
        Gets the render counter indication how many times the render method
        was called.
        """
        return self.__render_counter

    @property
    def cstruct(self):
        """
        Property returning the cstruct.
        """
        return self.__cstruct


class MockCallback(IFormValidationEvent):
    """
    Mock for form validation success and form validation failure callbacks.
    """

    def __init__(self, callback_result=None):
        """
        Initialises the MockCallback object.

        Args:
            callback_result: The optional result of the callback.
        """
        self.__callback_result = callback_result
        self.__request = None
        self.__result = None
        self.__appstruct = None
        self.__call_counter = 0


    def __call__(self, request, result, appstruct):
        """
        The mock callback storing the request, result and appstruct.

        Args:
            request: The Pyramid request which submitted the form.
            result: The view's result to which the form is rendered.
            appstruct: The data submitted to the form.

        Returns:
            The callback result set in the constructor.
        """
        self.__call_counter += 1
        self.__request = request
        self.__result = result
        self.__appstruct = appstruct
        return self.__callback_result

    def get_request(self):
        """
        Gets the request passed to the call method.

        Returns:
            The request passed to the call method.
        """
        return self.__request

    def get_result(self):
        """
        Gets the result passed to the call method.

        Returns:
            The result passed to the call method.
        """
        return self.__result

    def get_appstruct(self):
        """
        Gets the appstruct passed to the call method.

        Returns:
            The appstruct passed to the call method.
        """
        return self.__appstruct

    def get_call_counter(self):
        """
        Gets the call counter indicating how many times the call method was
        called.
        """
        return self.__call_counter


class TestIFormValidationEvent(unittest.TestCase):
    """
    Tests the IFormValidationEvent class.
    """

    def test_call(self):
        """
        Tests the call method of the IFormValidationEvent object.
        """
        event = IFormValidationEvent()
        with self.assertRaises(NotImplementedError):
            event(1, 2, 3)


class TestMultipleFormRenderer(unittest.TestCase):
    """
    Tests the MultipleFormRenderer class.
    """

    def tearDown(self):
        """
        Restore multiple_form_renderer.ValidationFailure
        """
        multiple_form_renderer.ValidationFailure = ValidationFailure

    @classmethod
    def create_form(cls, form_id, validate_appstruct=None):
        """
        Creates a dummy form.

        Args:
            form_id: The id of the dummy form.
            validate_appstruct: The optional appstruct being returned by
                form.validate().

        Return:
            The dummy form.
        """
        form = mock.Mock()
        form.formid = form_id
        form.validate.return_value = validate_appstruct
        return form

    @classmethod
    def create_form_validation_failure(
            cls, form, render_result=None, cstruct=None):
        """
        Creates a form validation failure.

        Args:
            form: The form which raises the validation failure.
            render_result: The optional result of the form rendering.
            cstruct: The optional cstruct returned by the rendering of the
                validation failure.

        Return:
            The validation_failure exception which is being raised by the form
            validation.
        """
        multiple_form_renderer.ValidationFailure = MockValidationFailure
        validation_failure = MockValidationFailure(render_result, cstruct)
        form.validate.side_effect = validation_failure
        return validation_failure

    @classmethod
    def create_post_request(cls, form):
        """
        Creates a post request for the form.

        Args:
            form: The form submitted with the post request.

        Returns:
            The post request.
        """
        request = mock.Mock()
        request.POST = {'__formid__': form.formid}
        request.method = 'POST'
        return request

    @classmethod
    def create_get_request(cls):
        """
        Creates a get request.

        Return:
            The get request.
        """
        request = mock.Mock()
        request.method = 'GET'
        return request

    def test_add_one_form(self):
        """
        Tests the MultipleFormRenderer.add() method by adding one single form.
        """
        form = self.create_form('dummy_form')
        request = self.create_get_request()
        result = {'test': 'value'}

        renderer = MultipleFormRenderer()
        renderer.add_form(form)
        render_result = renderer.render(request, result)

        # render_result contains result and rendered form
        self.assertEqual(len(render_result), 2)
        # result in render_result
        self.assertTrue('test' in render_result)
        self.assertEqual(render_result['test'], 'value')
        # form rendered to render_result
        self.assertTrue('dummy_form' in render_result)
        form.render.assert_called_once_with()

    def test_add_two_forms(self):
        """
        Tests the MultipleFormRenderer.add() method by adding two forms.
        """
        form1 = self.create_form('dummy_form1')
        form2 = self.create_form('dummy_form2')
        request = self.create_get_request()
        result = {'test': 'value'}

        renderer = MultipleFormRenderer()
        renderer.add_form(form1)
        renderer.add_form(form2)
        render_result = renderer.render(request, result)

        # render_result contains result and rendered forms
        self.assertEqual(len(render_result), 3)
        # result in render_result
        self.assertTrue('test' in render_result)
        self.assertEqual(render_result['test'], 'value')
        # form rendered to render_result
        self.assertTrue('dummy_form1' in render_result)
        self.assertTrue('dummy_form2' in render_result)
        form1.render.assert_called_once_with()
        form2.render.assert_called_once_with()

    def test_render_get(self):
        """
        Test the form rendering with a get request.
        """
        form = self.create_form('dummy_form')
        request = self.create_get_request()
        result = {'test': 'value'}

        renderer = MultipleFormRenderer()
        renderer.add_form(form)
        render_result = renderer.render(request, result)

        # render_result contains result and rendered form
        self.assertEqual(len(render_result), 2)
        # result in render_result
        self.assertTrue('test' in render_result)
        self.assertEqual(render_result['test'], 'value')
        # form rendered to render_result
        self.assertTrue('dummy_form' in render_result)
        form.render.assert_has_calls([mock.call()])

    def test_render_post(self):
        """
        Tests the form rendering and form validation with a post request.
        """
        form1 = self.create_form('dummy_form1')
        form2 = self.create_form('dummy_form2')
        request = self.create_post_request(form1)
        result = {'test': 'value'}

        renderer = MultipleFormRenderer()
        renderer.add_form(form1)
        renderer.add_form(form2)
        render_result = renderer.render(request, result)

        # render_result contains result and rendered forms
        self.assertEqual(len(render_result), 3)
        # result in render_result
        self.assertTrue('test' in render_result)
        self.assertEqual(render_result['test'], 'value')
        # forms rendered
        self.assertTrue('dummy_form1' in render_result)
        self.assertTrue('dummy_form2' in render_result)
        form1.render.assert_has_calls([mock.call()])
        form2.render.assert_has_calls([mock.call()])
        # validation called with POST items
        form1.validate.assert_has_calls([mock.call(request.POST.items())])

    def test_render_post_valid_exc(self):
        """
        Tests the form rendering and validation with a validateion failure
        exception.
        """
        form = self.create_form('dummy_form')
        validation_failure = self.create_form_validation_failure(
            form,
            'rendered_invalid_form')
        request = self.create_post_request(form)

        renderer = MultipleFormRenderer()
        renderer.add_form(form)
        render_result = renderer.render(request, {})

        # render_result contains rendered form
        self.assertEqual(len(render_result), 1)
        # forms rendered with validation failure
        self.assertTrue('dummy_form' in render_result)
        form.render.assert_has_calls([mock.call()])
        self.assertEqual(render_result['dummy_form'], 'rendered_invalid_form')
        # form validation failure rendered
        self.assertEqual(validation_failure.get_render_counter(), 1)

    def test_render_post_succ_callback(self):
        """
        Tests the form validation success callback.
        """
        validate_appstruct = {'dummy_validate_appstruct': 'dummy_value'}
        form = self.create_form('dummy_form', validate_appstruct)
        request = self.create_post_request(form)
        result = {'test': 'value'}
        validation_success_callback = MockCallback('success_result')

        renderer = MultipleFormRenderer()
        renderer.add_form(form, validation_success=validation_success_callback)
        render_result = renderer.render(request, result)

        # validation success callback called
        self.assertEqual(validation_success_callback.get_call_counter(), 1)
        # request passed to callback
        self.assertEqual(validation_success_callback.get_request(), request)
        # result passed to callback
        self.assertEqual(len(validation_success_callback.get_result()), 2)
        self.assertTrue(
            'dummy_form' in validation_success_callback.get_result())
        self.assertTrue('test' in validation_success_callback.get_result())
        self.assertEqual(
            validation_success_callback.get_result()['test'],
            'value')
        # validation appstruct passed to callback
        self.assertEqual(
            validation_success_callback.get_appstruct(),
            validate_appstruct)
        # render_result equals validation success callback result
        self.assertEqual(render_result, 'success_result')

    def test_render_post_fail_callback(self):
        """
        Tests the form validation failure callback.
        """
        form = self.create_form('dummy_form')
        cstruct = {'dummy_cstruct': 'dummy_value'}
        form_validation_failure = self.create_form_validation_failure(
            form,
            cstruct=cstruct)
        request = self.create_post_request(form)
        result = {'test': 'value'}
        validation_failure_callback = MockCallback('failure_result')

        renderer = MultipleFormRenderer()
        renderer.add_form(form, validation_failure=validation_failure_callback)
        render_result = renderer.render(request, result)

        # validation failure occured
        self.assertEqual(form_validation_failure.get_render_counter(), 1)
        # validation failure callback called
        self.assertEqual(validation_failure_callback.get_call_counter(), 1)
        # request passed to callback
        self.assertEqual(validation_failure_callback.get_request(), request)
        # result passed to callback
        self.assertEqual(len(validation_failure_callback.get_result()), 2)
        self.assertTrue(
            'dummy_form' in validation_failure_callback.get_result())
        self.assertTrue('test' in validation_failure_callback.get_result())
        self.assertEqual(
            validation_failure_callback.get_result()['test'],
            'value')
        # validation appstruct passed to callback
        self.assertEqual(validation_failure_callback.get_appstruct(), cstruct)
        # render_result equals validation failure callback result
        self.assertEqual(render_result, 'failure_result')
