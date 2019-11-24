# -*- coding: utf-8 -*-
"""
Test the c3smembership.presentation.schemas.dues module
"""

from unittest import TestCase

import deform
import mock

from c3smembership.presentation.schemas.dues import (
    invoice_archiving_year_widget,
    create_archiving_form,
)


class TestDuesSchema(TestCase):
    """
    Test the dues schema
    """

    def test_invoice_archiving_year_widget(self):
        """
        TEst the invoice_archiving_year_widget method
        """
        years = [
            (2015, 2015),
            (2016, 2016),
        ]
        widget = invoice_archiving_year_widget(None, {'years': years})
        self.assertTrue(isinstance(widget, deform.widget.SelectWidget))
        self.assertEqual(widget.values, years)

    def test_create_archiving_form(self):
        """
        Test the create_archiving_form method
        """
        request = mock.Mock()
        request.registry.dues_invoice_archiving.get_configured_years \
            .side_effect = [[2015, 2016]]
        form = create_archiving_form(request)
        self.assertTrue(isinstance(form, deform.form.Form))
