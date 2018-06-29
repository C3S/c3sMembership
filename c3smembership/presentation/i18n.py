# -*- coding: utf-8 -*-
"""Tools for user interface internationalization.

This package contains the translator factory "_" as well as the ZPT_RENDERER
factory for deform forms.
"""

from translationstring import TranslationStringFactory
from pyramid.i18n import (
    get_localizer,
)
from pyramid.threadlocal import get_current_request
from pkg_resources import resource_filename
import deform


_ = TranslationStringFactory('c3smembership')


def translator(term):
    """
    Template translator.
    """
    return get_localizer(get_current_request()).translate(term)

MY_TEMPLATE_DIR = resource_filename('c3smembership', 'templates')
MEMBERSHIP_DEFORM_TEMPLATES = resource_filename(
    'c3smembership',
    'presentation/templates/deform')
DEFORM_TEMPLATE_DIR = resource_filename('deform', 'templates')

ZPT_RENDERER = deform.ZPTRendererFactory(
    [
        MEMBERSHIP_DEFORM_TEMPLATES,
        MY_TEMPLATE_DIR,
        DEFORM_TEMPLATE_DIR,
    ],
    translator=translator,
)
