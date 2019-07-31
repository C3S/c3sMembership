# -*- coding: utf-8 -*-
"""
Add pre- and post-processing options to ``pyramid.view.view_config``

View Processing is used to perform per- and post-processing on
``pyramid.view.view_config`` methods. Pre-processing is performed before the
view callable is executed and post-processing thereafter.

Pre-processing can be used to handle ``pyramid.request.Request`` data like GET,
POST and url pattern matchdict.

Post-processing can be used to handle ``pyramid.response.Response`` object
before rendering.

One major use of pre-processing is validation. It offers a way to validate and
transform data passed via HTTP URL, GET and POST. Data passed via HTTP is
insecure as it can be manually edited. Therefore, validation is necessary in
order to prevent attacks like SQL injection.

Validation builds on to of colander and provides tools to simply use colander
validation. Following the separation of concerns pattern validation and object
conversion can be separated from the actual view definition to make the code
more readable and organized.

In addition the object conversion provides convinience when working with
objects which retrieved based on data passed via HTTP. Using validation these
objects are already validated and converted into the target object type.
"""

# pylint: disable=relative-import
import colander_validation
import error_handling
import post_processing
import pre_processing
import validation_node


ColanderGetValidator = colander_validation.ColanderGetValidator
ColanderMatchdictValidator = colander_validation.ColanderMatchdictValidator
ColanderPostValidator = colander_validation.ColanderPostValidator
ColanderValidator = colander_validation.ColanderValidator

ErrorHandler = error_handling.ErrorHandler
FlashCallbackErrorHandler = error_handling.FlashCallbackErrorHandler
FlashErrorHandler = error_handling.FlashErrorHandler
MultiErrorHandler = error_handling.MultiErrorHandler

MultiPostProcessor = post_processing.MultiPostProcessor
PostProcessor = post_processing.PostProcessor

MultiPreProcessor = pre_processing.MultiPreProcessor
PreProcessor = pre_processing.PreProcessor

ValidationNode = validation_node.ValidationNode


def processing_deriver(view, info):
    """
    Pyramid deriver handling pre- and post-processing

    The deriver hooks into Pyramid to handle the optional pre_processor and
    post_processor attributes of a view_config.
    """
    pre_processor = info.options.get('pre_processor')
    post_processor = info.options.get('post_processor')

    def view_wrapper(context, request):
        """
        Wrap the pyramid view and do pre- and post-processing

        If the pre-processor returns a value it is returned immediately and the
        view is not called at all. If the post-processor returns a value then
        it is returned instead of the view's Response object.
        """
        if pre_processor is not None:
            result = pre_processor(context, request)
            if result is not None:
                return result
        response = view(context, request)
        if post_processor is not None:
            result = post_processor(response, context, request)
            if result is not None:
                return result
        return response

    return view_wrapper


processing_deriver.options = ('pre_processor', 'post_processor',)


def set_colander_error_handler(config, error_handler):
    """
    Add a default Colander error handler to the view_processing settings

    The error handler must implement the ``view_processing.ErrorHandler``
    interface.

    This function is added as a directive to the Pyramid config to be called on
    application setup.

    Example:

        ::

            def default_error_handler(request, schema, errors):
                print('Error found')

            from pyramid.config import Configurator
            config = Configurator()
            config.set_colander_error_handler(default_error_handler)

    Example:

        ::

            class DefaultErrorHandler(view_processing.ErrorHandler):

                def __call__(self, request, schema, errors):
                    print('Error found')

            from pyramid.config import Configurator
            config = Configurator()
            config.set_colander_error_handler(DefaultErrorHandler())
    """
    config.registry.view_processing['error_handler'] = error_handler


def includeme(config):
    """
    Hook processing as a plugin into pyramid

    This method is called when the plugin is included into the pyramid
    application's configuration using the ``pyramid.Configurator.include()``
    method. It is not necessary to call this method directly.

    Example:

        ::

            from pyramid.config import Configurator
            config = Configurator()
            config.include('view_processing')

    A custom view deriver is hooked into Pyramid to handle pre- and
    post-processing.

    See also:

    - https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#custom-view-derivers
    - https://docs.pylonsproject.org/projects/pyramid/en/latest/glossary.html#term-view-deriver
    """
    config.registry.view_processing = {}
    config.add_directive(
        'set_colander_error_handler', set_colander_error_handler)
    config.add_view_deriver(processing_deriver)
