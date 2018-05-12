# -*- coding: utf-8 -*-
"""
Provides tools for handling tex files.
"""

import re


class TexTools(object):
    """
    Provides tools for handling tex files.
    """

    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
        u'℅': r'c/o',
        u'°': r'\degree{}',
        u'ß': r'\ss{}',
    }
    regex = re.compile(u'|'.join(re.escape(key)
                       for key in sorted(
                           conv.keys(),
                           key=lambda item: -len(item))))

    @classmethod
    def escape(cls, text):
        """
        Escape strings to make them TeX compatible.
        """
        # TODO: General rule to handle latex incompatible unicode characters
        # needed.
        if text is None:
            return None
        else:
            return cls.regex.sub(lambda match: cls.conv[match.group()], text)
