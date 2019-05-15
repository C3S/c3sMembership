# -*- coding: utf-8 -*-
"""
Schemas for general assembly creation and editing.
"""
import datetime

import colander
import deform

from c3smembership.presentation.i18n import ZPT_RENDERER
from c3smembership.presentation.schemas.member import MemberNode
from c3smembership.presentation.view_processing import ValidationNode


class GeneralAssemblySchemaGroup(colander.Schema):
    """
    General assembly creation and editing schema.
    """
    number = colander.SchemaNode(
        colander.Integer(),
        title=u'Number',
        oid='number',
        widget=deform.widget.TextInputWidget(readonly=True),
        missing=None)
    name = colander.SchemaNode(
        colander.String(),
        title=u'Name',
        oid='name')
    date = colander.SchemaNode(
        colander.Date(),
        title='Date',
        validator=colander.Range(
            min=datetime.date.today(),
            min_err=u'${val} is in the past. The general assembly must take '
                    u'place in the future.'),
        default=datetime.date.today())


class GeneralAssemblySchema(colander.Schema):
    """
    General assembly creation and editing form.
    """
    general_assembly = GeneralAssemblySchemaGroup(
        title='General assembly')


class GeneralAssemblyNode(ValidationNode):
    """
    Colander SchemaNode for a general assembly

    The general assembly is represented by a general assembly number. If the
    number is valid it is converted into a general assembly object.
    """

    schema_type = colander.Int
    validation_error_message = 'General assembly {} does not exist.'
    new_name = 'general_assembly'

    def transform(self, request, value):
        return request.registry.general_assembly_invitation \
            .get_general_assembly(value)


class GeneralAssemblyMatchdict(colander.MappingSchema):
    """
    Schema for validating the general assembly matchdict

    The general assembly number has the name 'number'. If the number is valid,
    the corresponding general assembly object is retrieved.
    """
    number = GeneralAssemblyNode()


class GeneralAssemblyInvitationMatchdict(colander.MappingSchema):
    """
    Schema for validating the general assembly invitation matchdict

    The matchdict contains:

    - General assembly number 'number' if valid transformed into a general
      assembly object named 'general_assembly'
    - Membership number 'membership_number' if valid transformed into a member
      object named 'member'
    """
    number = GeneralAssemblyNode()
    membership_number = MemberNode()


class BatchInvitePost(colander.MappingSchema):
    """
    Schema for validating batch invite POST data

    The POST data contains a count integer with a minimum of 1 and a default
    value of 5.
    """
    count = colander.SchemaNode(
        colander.Int(),
        missing=5,
        pre_processor=colander.Range(min=1))


class GeneralAssemblyFormFactory(object):
    """
    Factory creating general assembly Deform forms
    """
    # pylint: disable=too-few-public-methods

    @classmethod
    def create(cls):
        """
        Create a general assembly form
        """
        return deform.Form(
            GeneralAssemblySchema(),
            buttons=[
                deform.Button('submit', u'Submit'),
                deform.Button('reset', u'Reset'),
                deform.Button('cancel', u'Cancel'),
            ],
            renderer=ZPT_RENDERER,
            use_ajax=True,
        )
