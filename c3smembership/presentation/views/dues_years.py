# -*- coding: utf-8 -*-
"""
Configured membership dues years.

This dependency-free module is the single place defining which dues years exist.
To support a following year, bump ``LATEST_DUES_YEAR`` and provide the LaTeX
templates (``certificate/<template>/duesNN_*.tex``). No data model or per-year
code change is required.
"""

# The most recent dues year.
LATEST_DUES_YEAR = 2025

# All dues years in ascending order.
DUES_YEARS = list(range(2015, LATEST_DUES_YEAR + 1))
