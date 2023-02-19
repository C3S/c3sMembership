# -*- coding: utf-8 -*-
"""
Test module for c3smembership.tex_tools.
"""

import unittest
from c3smembership.tex_tools import TexTools


class TestTexTools(unittest.TestCase):
    """
    Test module for c3smembership.tex_tools.
    """

    def test_escape(self):
        """
        Test method TexTools.escape
        """
        unescaped = '&%$#_{}~^\\<>℅°ß'
        escaped = TexTools.escape(unescaped)
        expected = '\\&\\%\\$\\#\\_\\{\}\\textasciitilde{}\\^{}' + \
                   '\\textbackslash{}\\textless{}\\textgreater{}c/o\\degree{}\\ss{}'
        self.assertEqual(escaped, expected)
