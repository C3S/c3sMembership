# -*- coding: utf-8 -*-
"""
Validate request GET, POST and url pattern matchdict data using a Colander
schema
"""

import colander

from c3smembership.presentation.view_processing.pre_processing import \
    PreProcessor


class ColanderValidator(PreProcessor):
    """
    Validate request data based on a Colander schema

    Schema nodes are renamed if they have a new_name attribute. This is
    especially meaningful if the data is not only validated but also
    transformed, e.g. returning a retrieved object based on an attribute
    passed.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, schema, error_handler=None):
        self.schema = schema
        self.error_handler = error_handler

    def __call__(self, context, request):
        try:
            data = self.schema \
                .bind(request=request) \
                .deserialize(self.get_data(request))
            data = self._rename_nodes(data, self.schema)
            self.set_data(request, data)
        except colander.Invalid as validation_error:
            errors = validation_error.asdict()
            result = None

            self_has_error_handler = self.error_handler is not None
            schema_has_error_handler = hasattr(self.schema, 'error_handler')
            settings_have_error_handler = (
                hasattr(request, 'registry') and
                hasattr(request.registry, 'view_processing') and
                'error_handler' in request.registry.view_processing)

            if self_has_error_handler:
                result = self.error_handler(request, self.schema, errors)
            elif schema_has_error_handler:
                result = self.schema.error_handler(
                    request, self.schema, errors)
            elif settings_have_error_handler:
                settings_error_handler = request.registry.view_processing[
                    'error_handler']
                result = settings_error_handler(request, self.schema, errors)
            else:
                # pass on validation error if no error handler specified
                raise validation_error

            return result

    def get_data(self, request):
        """
        Get the data to be validated using the schema
        """
        raise NotImplementedError()

    def set_data(self, request, data):
        """
        Set the validated data
        """
        raise NotImplementedError()

    @classmethod
    def _rename_nodes(cls, data, schema):
        """
        Rename nodes according to their new_name attribute if present
        """
        for child in schema.children:
            if (hasattr(child, 'new_name') and child.new_name is not None and
                    child.name != child.new_name):
                value = data[child.name]
                del data[child.name]
                data[child.new_name] = value
        return data


class ColanderMatchdictValidator(ColanderValidator):
    """
    Validate route matching URL pattern from request.matchdict via a Colander
    schema

    The validated matchdict data can be used via request.validated_matchdict.
    """
    # pylint: disable=too-few-public-methods

    def get_data(self, request):
        """
        Get the data to be validated from request.matchdict
        """
        return request.matchdict

    def set_data(self, request, data):
        """
        Set the data to be validated to request.validated_matchdict
        """
        request.validated_matchdict = data


class ColanderPostValidator(ColanderValidator):
    """
    Validate POST data from request.POST via a Colander schema

    The validated POST data can be used via request.validated_post.
    """
    # pylint: disable=too-few-public-methods

    def get_data(self, request):
        """
        Get the data to be validated from request.POST
        """
        return request.POST

    def set_data(self, request, data):
        """
        Set the data to be validated to request.validated_post
        """
        request.validated_post = data


class ColanderGetValidator(ColanderValidator):
    """
    Validate GET data from request.GET via a Colander schema

    The validated GET data can be used via request.validated_get.
    """
    # pylint: disable=too-few-public-methods

    def get_data(self, request):
        """
        Get the data to be validated from request.GET
        """
        return request.GET

    def set_data(self, request, data):
        """
        Set the data to be validated to request.validated_get
        """
        request.validated_get = data
