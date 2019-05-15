# -*- coding: utf-8 -*-
"""
Member schema definitions
"""

import colander

from c3smembership.presentation.view_processing import ValidationNode


class MemberNode(ValidationNode):
    """
    Define a Colander schema node for members

    The schema node validates a membership number and transforms it into a
    member object.
    """

    schema_type = colander.Int
    validation_error_message = 'Membership number {} does not exist.'
    new_name = 'member'

    def transform(self, request, value):
        return request.registry.member_information.get_member(value)
