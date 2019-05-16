# -*- coding: utf-8 -*-
"""
Member schema definitions
"""

import colander

from c3smembership.presentation.view_processing import ValidationNode


class MemberNode(ValidationNode):
    """
    Define a Colander schema node for member by membership number

    The schema node validates a membership number and transforms it into a
    member object.
    """

    schema_type = colander.Int
    validation_error_message = 'Membership number {} does not exist.'
    new_name = 'member'

    def transform(self, request, value):
        """
        Transform the validated membership number into a member object
        """
        return request.registry.member_information.get_member(value)


class MemberIdNode(ValidationNode):
    """
    Define a Colander schema node for member by member ID

    The schema node validates a membership id and transforms it into a member
    object.

    The schema node only exists for legacy reasons. The presentation layer
    should not deal with database IDs but with the business keys instead which
    is the membership number for which the MemberNode class exists.
    """

    schema_type = colander.Int
    validation_error_message = 'Member ID {} does not exist.'
    new_name = 'member'

    def transform(self, request, value):
        """
        Transform the validated member ID into a member object
        """
        return request.registry.member_information.get_member_by_id(value)


class MemberIdIsMemberNode(MemberIdNode):
    """
    Define a Colander schema node for member with membership by member ID

    The schema node validates a membership id, transforms it into a member
    object and verifies that membership was granted.

    The schema node only exists for legacy reasons. The presentation layer
    should not deal with database IDs but with the business keys instead which
    is the membership number for which the MemberNode class exists.
    """

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
        super(MemberIdIsMemberNode, self).validate(request, value)
        if not value.is_member():
            message = \
                u'Member with member ID {} has not been granted membership'
            raise colander.Invalid(
                self,
                message.format(self.original_value))


class MemberIdMatchdict(colander.MappingSchema):
    """
    Schema for validating a member ID Matchdict

    The member ID has is valid as an integer and turned into a member object.
    """
    member_id = MemberIdNode()


class MailCertificateMatchdict(colander.MappingSchema):
    """
    Schema for validating the mail certificate matchdict

    The member ID has is valid as an integer and turned into a member object.
    """
    member_id = MemberIdIsMemberNode()


class GenerateCertificateMatchdict(colander.MappingSchema):
    """
    Schema for validating the generate certificate matchdict

    The member ID has is valid as an integer and turned into a member object.
    The token is a string.
    """
    member_id = MemberIdIsMemberNode()
    token = colander.SchemaNode(colander.String)
