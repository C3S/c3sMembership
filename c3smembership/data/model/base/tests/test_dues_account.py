# -*- coding: utf-8  -*-
"""
Tests for the Dues account model.
"""

from datetime import (
    date,
    datetime,
)
from decimal import Decimal
import unittest

from sqlalchemy import engine_from_config
from sqlalchemy.exc import IntegrityError

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.dues import Dues


class TestDuesModel(unittest.TestCase):
    """
    Tests the Dues account model.
    """

    def setUp(self):
        engine = engine_from_config({'sqlalchemy.url': 'sqlite:///:memory:'})
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.db_session.close()
        DBSession.remove()

    def test_defaults(self):
        """
        A fresh, non-persisted account has sensible default values.
        """
        dues = Dues(member_id=1, year=2026)
        self.assertEqual(dues.year, 2026)
        self.assertFalse(dues.invoice)
        self.assertFalse(dues.paid)
        self.assertFalse(dues.reduced)
        self.assertTrue(dues.balanced)
        self.assertTrue(dues.amount.is_nan())
        self.assertTrue(dues.amount_reduced.is_nan())
        self.assertEqual(dues.balance, Decimal('0'))
        self.assertEqual(dues.amount_paid, Decimal('0'))

    def test_balance_sets_balanced_flag(self):
        """
        Setting the balance updates the balanced flag.
        """
        dues = Dues(member_id=1, year=2026)
        dues.balance = Decimal('50')
        self.assertEqual(dues.balance, Decimal('50'))
        self.assertFalse(dues.balanced)

        dues.balance = Decimal('0')
        self.assertTrue(dues.balanced)

    def test_amount_reduced_sets_reduced_flag(self):
        """
        Setting the reduced amount updates the reduced flag.
        """
        dues = Dues(member_id=1, year=2026)
        dues.amount = Decimal('50')

        # reduced amount equal to amount does not count as reduced
        dues.amount_reduced = Decimal('50')
        self.assertFalse(dues.reduced)

        # a different reduced amount counts as reduced
        dues.amount_reduced = Decimal('20')
        self.assertTrue(dues.reduced)

        # NaN reduced amount does not count as reduced
        dues.amount_reduced = Decimal('NaN')
        self.assertFalse(dues.reduced)

    def test_set_amount(self):
        """
        set_amount sets the amount and adjusts the balance.
        """
        dues = Dues(member_id=1, year=2026)
        dues.set_amount(Decimal('50'))
        self.assertEqual(dues.amount, Decimal('50'))
        self.assertEqual(dues.balance, Decimal('50'))
        self.assertFalse(dues.balanced)

        # setting the amount again replaces it in the balance, not accumulates
        dues.set_amount(Decimal('30'))
        self.assertEqual(dues.amount, Decimal('30'))
        self.assertEqual(dues.balance, Decimal('30'))

    def test_set_payment(self):
        """
        set_payment accumulates the paid amount and reduces the balance.
        """
        dues = Dues(member_id=1, year=2026)
        dues.set_amount(Decimal('50'))

        dues.set_payment(Decimal('20'), datetime(2026, 5, 1))
        self.assertTrue(dues.paid)
        self.assertEqual(dues.amount_paid, Decimal('20'))
        self.assertEqual(dues.paid_date, datetime(2026, 5, 1))
        self.assertEqual(dues.balance, Decimal('30'))
        self.assertFalse(dues.balanced)

        # a second payment accumulates and settles the balance
        dues.set_payment(Decimal('30'), datetime(2026, 6, 1))
        self.assertEqual(dues.amount_paid, Decimal('50'))
        self.assertEqual(dues.balance, Decimal('0'))
        self.assertTrue(dues.balanced)

    def test_set_reduced_amount(self):
        """
        set_reduced_amount adjusts amount_reduced and balance.
        """
        dues = Dues(member_id=1, year=2026)
        dues.set_amount(Decimal('50'))

        dues.set_reduced_amount(Decimal('20'))
        self.assertTrue(dues.reduced)
        self.assertEqual(dues.amount_reduced, Decimal('20'))
        self.assertEqual(dues.balance, Decimal('20'))

        # reducing again replaces the previous reduced amount in the balance
        dues.set_reduced_amount(Decimal('10'))
        self.assertEqual(dues.amount_reduced, Decimal('10'))
        self.assertEqual(dues.balance, Decimal('10'))

        # setting the reduced amount back to the full amount clears the reduction
        dues.set_reduced_amount(Decimal('50'))
        self.assertFalse(dues.reduced)
        self.assertTrue(dues.amount_reduced.is_nan())

    def test_unique_member_year(self):
        """
        There can only be one dues account per member and year.
        """
        self.db_session.add(Dues(member_id=1, year=2026))
        self.db_session.flush()
        self.db_session.add(Dues(member_id=1, year=2026))
        with self.assertRaises(IntegrityError):
            self.db_session.flush()
        self.db_session.rollback()

    def test_distinct_member_year_allowed(self):
        """
        Different members or years can coexist.
        """
        self.db_session.add(Dues(member_id=1, year=2025))
        self.db_session.add(Dues(member_id=1, year=2026))
        self.db_session.add(Dues(member_id=2, year=2026))
        self.db_session.flush()
        self.assertEqual(self.db_session.query(Dues).count(), 3)
