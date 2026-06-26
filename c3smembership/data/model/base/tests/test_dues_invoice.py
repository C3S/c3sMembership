# -*- coding: utf-8  -*-
"""
Tests for the DuesInvoice model.
"""

from datetime import datetime
from decimal import Decimal
import unittest

from sqlalchemy import engine_from_config
from sqlalchemy.exc import IntegrityError

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.dues_invoice import DuesInvoice


def _invoice(year, invoice_no, invoice_no_string):
    return DuesInvoice(
        year=year,
        invoice_no=invoice_no,
        invoice_no_string=invoice_no_string,
        invoice_date=datetime(year, 2, 1),
        invoice_amount=Decimal('50.0'),
        member_id=1,
        membership_no=9,
        email='member@example.com',
        token='TOKEN12345')


class TestDuesInvoiceModel(unittest.TestCase):
    """
    Tests the DuesInvoice model.
    """

    def setUp(self):
        engine = engine_from_config({'sqlalchemy.url': 'sqlite:///:memory:'})
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.db_session.close()
        DBSession.remove()

    def test_create_and_read(self):
        """
        An invoice can be created, persisted and read back.
        """
        self.db_session.add(_invoice(2026, 1, 'C3S-dues2026-0001'))
        self.db_session.flush()
        invoice = self.db_session.query(DuesInvoice).one()
        self.assertEqual(invoice.year, 2026)
        self.assertEqual(invoice.invoice_no, 1)
        self.assertEqual(invoice.invoice_no_string, 'C3S-dues2026-0001')
        self.assertEqual(invoice.invoice_amount, Decimal('50.0'))

    def test_invoice_no_unique_per_year(self):
        """
        The invoice number is unique within a year but may repeat across years.
        """
        # same invoice_no in different years is allowed
        self.db_session.add(_invoice(2025, 1, 'C3S-dues2025-0001'))
        self.db_session.add(_invoice(2026, 1, 'C3S-dues2026-0001'))
        self.db_session.flush()
        self.assertEqual(self.db_session.query(DuesInvoice).count(), 2)

        # same invoice_no in the same year is rejected
        self.db_session.add(_invoice(2026, 1, 'C3S-dues2026-0001-dup'))
        with self.assertRaises(IntegrityError):
            self.db_session.flush()
        self.db_session.rollback()

    def test_invoice_no_string_unique_per_year(self):
        """
        The invoice number string is unique within a year.
        """
        self.db_session.add(_invoice(2026, 1, 'C3S-dues2026-0001'))
        self.db_session.flush()
        self.db_session.add(_invoice(2026, 2, 'C3S-dues2026-0001'))
        with self.assertRaises(IntegrityError):
            self.db_session.flush()
        self.db_session.rollback()
