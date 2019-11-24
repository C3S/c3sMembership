# -*- coding: utf-8 -*-
"""
Post-processor for handling view call responses
"""


class PostProcessor(object):
    """
    Post process view calls
    """
    # pylint: disable=too-few-public-methods

    def __call__(self, response, context, request):
        """
        Process view calls

        Args:
            response: The ``pyramid.response.Response`` produced by Pyramid
                from the view's results
            context: The ``context`` passed to the view
            request: The ``pyramid.request.Request`` which the view handled
        """
        raise NotImplementedError()


class MultiPostProcessor(PostProcessor):
    """
    Use multiple post-processors
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, post_processors):
        """
        Initialise the MultiPostProcessor object

        Args:
            post_processors: An iterable containing objects implementing the
                ``PostProcessor`` interface
        """
        self._post_processors = post_processors

    def __call__(self, response, context, request):
        """
        Process view calls via the post-processors passed during object
        initialisation

        Args:
            response: The ``pyramid.response.Response`` produced by Pyramid
                from the view's results
            context: The ``context`` passed to the view
            request: The ``pyramid.request.Request`` which the view handled
        """
        for post_processor in self._post_processors:
            result = post_processor(response, context, request)
            if result is not None:
                return result
