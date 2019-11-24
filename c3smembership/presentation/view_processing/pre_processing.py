# -*- coding: utf-8 -*-
"""
Pre-processor for handling view calls
"""


class PreProcessor(object):
    """
    Pre process view calls
    """
    # pylint: disable=too-few-public-methods

    def __call__(self, context, request):
        """
        Process view calls

        Args:
            context: The ``context`` passed to the view
            request: The ``pyramid.request.Request`` which the view handled
        """
        raise NotImplementedError()


class MultiPreProcessor(PreProcessor):
    """
    Use multiple pre-processors
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, pre_processors):
        """
        Initialise the MultiPreProcessor object

        Args:
            pre_processors: An iterable containing objects implementing the
                ``PreProcessor`` interface
        """
        self._pre_processors = pre_processors

    def __call__(self, context, request):
        """
        Process view calls via the pre-processors passed during object
        initialisation

        Args:
            response: The ``pyramid.response.Response`` produced by Pyramid
                from the view's results
            context: The ``context`` passed to the view
            request: The ``pyramid.request.Request`` which the view handled
        """
        for pre_processor in self._pre_processors:
            result = pre_processor(context, request)
            if result is not None:
                return result
