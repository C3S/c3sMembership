# -*- coding: utf-8 -*-
"""
Provide a base class for ``colander.SchemaNode`` validation classes
"""

import colander


@colander.deferred
def deferred_preparer(node, keywords):
    """
    Deferred colander preparer calling the ValidationNode transform method

    Args:
        node: The ``colander.SchemaNode`` to which this preparer belongs
        keywords: The schema binding keywords

    Returns:
        A preparer callable.
    """

    def preparer(value):
        """
        Preparer callable using the node's transform method

        The preparer stores the value in the node's original_value attribute
        and calls the node's transform method.

        Args:
            value: The value of the colander.SchemaNode validated according to
                the schema type.

        Returns:
            The result of the node's transform method and returning it's
            result.
        """
        node.original_value = value
        return node.transform(keywords['request'], value)

    return preparer


@colander.deferred
def deferred_validator(node, keywords):
    """
    Deferred colander validator calling the ValidationNode validate method

    Args:
        node: The ``colander.SchemaNode`` to which this preparer belongs
        keywords: The schema binding keywords

    Returns:
        A validator callable.
    """
    # pylint: disable=unused-argument
    request = keywords['request']

    def validator(node, value):
        """
        Validator callable using the node's validate method

        Args:
            node: The ``colander.SchemaNode`` to which this preparer belongs
            value: The validated and prepared value

        Raises:
            ``colander.Invalid``: If the node's validate method returns
            anything but None a ``colander.Invalid`` exception is raised
            containing the validate method's result as an error message.
        """
        result = node.validate(request, value)
        if result is not None:
            raise colander.Invalid(node, result)

    return validator


class ValidationNode(colander.SchemaNode):
    """
    Base class for ``colander.SchemaNode`` validation classes

    The ValidationNode uses a deferred preparer calling the newly introduced
    transform method which can be used to transform an identifying number into
    the corresponding object. A deferred validator calls the validate method
    which by default checks that the value is not None. If the value is None a
    validation error message is raised as ``colander.Invalid`` exception.

    The node's original_value attribute can be used in the validate method to
    retrieve the validated value prior to transformation.

    Example::

        class MemberNode(ValidationNode):
            validation_error_message = 'Membership number {} does not exist'

            def transform(self, request, node, value):
                return request.member_information.get(value)

    Example::

        class ActiveMemberNode(ValidationNode):
            def transform(self, request, node, value):
                return request.member_information.get(value)

            def validate(self, request, node, value):
                member = value
                if not member.is_active:
                    raise colander.Invalid(
                        node,
                        '{} is not a member'.format(node.original_value))
    """
    # pylint: disable=abstract-method

    original_value = None
    preparer = deferred_preparer
    validation_error_message = '{} is not valid'
    validator = deferred_validator

    def transform(self, request, value):
        """
        Transform the validated value

        Args:
            request: The ``pyramid.request.Request`` which the validated data
                was passed to
            value: The validated value of the schema node

        Returns:
            The transformed value, e.g. an object which is identified by the
            original value. The default implementation returns the unmodified
            value.
        """
        # pylint: disable=unused-argument,no-self-use
        return value

    def validate(self, request, value):
        """
        Validate the transformed value

        Args:
            request: The ``pyramid.request.Request`` which the validated data
                was passed to
            value: The transformed value of the schema node

        Returns:
            Usually None. The validate method can raise ``colander.Invalid``
            exceptions in case of any validation errors. The default
            implementation raises an exception if the value is None using the
            node's validation_error_message attribute and the original value.

            The validation_error_message attribute can be set for a precise
            error message.

            If the method does return something it is used as a error message
            for a ``colander.Invalid`` exception raised.
        """
        # pylint: disable=unused-argument
        if value is None:
            raise colander.Invalid(
                self,
                self.validation_error_message.format(self.original_value))
