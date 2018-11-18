# -*- coding: utf-8 -*-
"""
Schemas for general assembly creation and editing.
"""
import datetime

import colander
import deform


class GeneralAssemblySchema(colander.Schema):
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


class GeneralAssemblyForm(colander.Schema):
    """
    General assembly creation and editing form.
    """
    general_assembly = GeneralAssemblySchema(
        title='General assembly')
