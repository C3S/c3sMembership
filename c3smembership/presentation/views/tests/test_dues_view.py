# -*- coding: utf-8 -*-
"""
Tests for the dues dashboard view, in particular the new-year readiness notice.
"""

from datetime import date
import os
import shutil
import tempfile
import unittest

from pyramid import testing

from c3smembership.presentation.views import dues_year
from c3smembership.presentation.views.dues import (
    dues,
    next_year_status,
)
from c3smembership.presentation.views.dues_years import LATEST_DUES_YEAR


class TestNextYearStatus(unittest.TestCase):
    """
    Tests the new-year detection and template readiness check.
    """

    def setUp(self):
        self.config = testing.setUp()
        # use a temporary certificate template directory
        self.template_root = tempfile.mkdtemp()
        self.template_name = 'unittest'
        os.makedirs(os.path.join(self.template_root, self.template_name))
        self._orig_pdflatex_dir = dues_year.PDFLATEX_DIR
        dues_year.PDFLATEX_DIR = self.template_root
        self.request = testing.DummyRequest()
        self.request.registry.settings = {
            'c3smembership.certificate_template': self.template_name,
        }

    def tearDown(self):
        dues_year.PDFLATEX_DIR = self._orig_pdflatex_dir
        shutil.rmtree(self.template_root, ignore_errors=True)
        testing.tearDown()

    def _create_templates(self, year, kinds):
        for kind in kinds:
            path = dues_year.latex_template(year, kind).format(
                self.template_name)
            with open(path, 'w') as template_file:
                template_file.write('% test template')

    def test_no_new_year(self):
        """
        While the current date is within a configured year there is no notice.
        """
        status = next_year_status(
            self.request, today=date(LATEST_DUES_YEAR, 6, 1))
        self.assertIsNone(status)

    def test_new_year_templates_missing(self):
        """
        When the new year has begun without templates, they are reported missing.
        """
        status = next_year_status(
            self.request, today=date(LATEST_DUES_YEAR + 1, 1, 1))
        self.assertIsNotNone(status)
        self.assertEqual(status['year'], LATEST_DUES_YEAR + 1)
        self.assertFalse(status['templates_ready'])
        self.assertEqual(len(status['missing_templates']), 4)

    def test_new_year_templates_present(self):
        """
        When all templates are present, the year is reported ready.
        """
        next_year = LATEST_DUES_YEAR + 1
        self._create_templates(
            next_year,
            ('invoice_de', 'invoice_en', 'storno_de', 'storno_en'))

        status = next_year_status(
            self.request, today=date(next_year, 3, 1))
        self.assertTrue(status['templates_ready'])
        self.assertEqual(status['missing_templates'], [])

    def test_new_year_templates_partially_present(self):
        """
        A partially configured year is not ready and lists only what is missing.
        """
        next_year = LATEST_DUES_YEAR + 1
        self._create_templates(next_year, ('invoice_de', 'invoice_en'))

        status = next_year_status(self.request, today=date(next_year, 3, 1))
        self.assertFalse(status['templates_ready'])
        self.assertEqual(
            sorted(status['missing_templates']),
            ['dues{0}_storno_de.tex'.format(next_year % 100),
             'dues{0}_storno_en.tex'.format(next_year % 100)])

    def test_view_exposes_notice(self):
        """
        The dues view exposes the notice fields to the template.
        """
        result = dues(self.request)
        self.assertIn('next_dues_year', result)
        self.assertIn('dues_years', result)
        self.assertEqual(result['latest_dues_year'], LATEST_DUES_YEAR)
