# -*- coding: utf-8 -*-
from pyramid.view import view_config
from c3smembership.presentation.parameter_validation import (
    ParameterValidationException
)


@view_config(
    context=ParameterValidationException,
    renderer='c3smembership.presentation:templates/pages/'
             'parameter_validation_exception.pt')
def parameter_validation_view(exc, request):
    """
    """
    message = 'Failed validation: {0}'.format(exc.message)
    request.response.status = 400
    return {
        'validation_failure_message': message,
        'redirect_url': exc.redirect_url,
        'refresh_time': 5,  # TODO: take from configuration
    }
