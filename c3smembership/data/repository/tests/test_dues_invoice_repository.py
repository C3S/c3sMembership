# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.dues_invoice_repository package.
"""

from datetime import (
    date,
    datetime,
)
from decimal import Decimal
import unittest

import transaction

from sqlalchemy import engine_from_config

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues import Dues
from c3smembership.data.model.base.dues_invoice import DuesInvoice
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository

from c3smembership.business.dues_calculation import DuesCalculation


def _invoice(year, **kwargs):
    """
    Build a DuesInvoice for the year filling in defaults.
    """
    defaults = dict(
        invoice_no_string='C3S-dues{0}-{1}'.format(
            year, str(kwargs['invoice_no']).zfill(4)),
        invoice_date=date(year, 2, 1),
        invoice_amount=Decimal('1234.{0}'.format(year % 100)),
        member_id=kwargs.pop('member_id', 1),
        membership_no=9,
        email='member1@example.com',
        token='{0}WXYZ7890'.format(year % 100),
    )
    defaults.update(kwargs)
    return DuesInvoice(year=year, **defaults)


class TestDuesInvoiceRepository(unittest.TestCase):
    """
    Tests the DuesInvoiceRepository class against the normalized dues tables.
    """
    def setUp(self):
        """
        Set up test cases
        """
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
        }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(
                firstname='SomeFirstnäme',
                lastname='SomeLastnäme',
                email='member1@example.com',
                address1='addr one',
                address2='addr two',
                postcode='12345',
                city='Footown Mäh',
                country='Foocountry',
                locale='DE',
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGFOO',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc='GEMA',
                num_shares=35,
            )
            member1.membership_number = 9
            member1.membership_date = date(2018, 1, 1)
            member1.membership_accepted = True
            self.db_session.add(member1)
            self.db_session.flush()

            # payments are stored on the per-year dues account
            payments = {
                2015: (date(2015, 10, 31), Decimal('15.11')),
                2016: (date(2016, 12, 31), Decimal('16.11')),
                2017: (date(2017, 11, 30), Decimal('17.11')),
                2018: (date(2018, 9, 30), Decimal('18.11')),
                2019: (date(2019, 11, 19), Decimal('19.11')),
                2020: (date(2020, 11, 20), Decimal('20.11')),
            }
            for year, (paid_date, amount) in payments.items():
                dues = member1.get_dues(year)
                dues.paid = True
                dues.paid_date = paid_date
                dues.amount_paid = amount

            # invoices across years in the single table
            self.db_session.add(_invoice(2015, invoice_no=2348,
                                         invoice_date=date(2015, 10, 1),
                                         invoice_amount=Decimal('9876.15')))
            self.db_session.add(_invoice(2016, invoice_no=1276,
                                         invoice_date=date(2016, 6, 16),
                                         invoice_amount=Decimal('9876.16')))
            self.db_session.add(_invoice(2017, invoice_no=7544,
                                         invoice_date=date(2017, 7, 17),
                                         invoice_amount=Decimal('9876.17')))

            # 2018: normal, reversal and reduced invoice
            original = _invoice(2018, invoice_no=9876,
                                invoice_date=date(2018, 1, 12),
                                invoice_amount=Decimal('9876.18'))
            original.is_cancelled = True
            original.cancelled_date = date(2018, 9, 18)
            self.db_session.add(original)
            reversal = _invoice(2018, invoice_no=9877,
                                invoice_date=date(2018, 9, 18),
                                invoice_amount=Decimal('-9876.18'))
            reversal.is_reversal = True
            self.db_session.add(reversal)
            reduced = _invoice(2018, invoice_no=9878,
                               invoice_date=date(2018, 9, 18),
                               invoice_amount=Decimal('5678.18'))
            reduced.is_altered = True
            self.db_session.add(reduced)

            self.db_session.add(_invoice(2019, invoice_no=1234,
                                         invoice_date=date(2019, 2, 24),
                                         invoice_amount=Decimal('1234.19')))
            self.db_session.add(_invoice(2020, invoice_no=2020,
                                         invoice_date=date(2020, 2, 24),
                                         invoice_amount=Decimal('1234.20')))
            self.db_session.flush()

    def tearDown(self):
        self.db_session.close()
        DBSession.remove()

    def test_get_all(self):
        """
        Test the get_all method
        """
        self.assertEqual(len(DuesInvoiceRepository.get_all()), 8)
        self.assertEqual(len(DuesInvoiceRepository.get_all([])), 0)

        invoices = DuesInvoiceRepository.get_all([2015])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 2348)

        invoices = DuesInvoiceRepository.get_all([2018])
        self.assertEqual(len(invoices), 3)
        self.assertEqual(
            sorted(i.invoice_no for i in invoices), [9876, 9877, 9878])

        invoices = DuesInvoiceRepository.get_all([2015, 2016, 2020])
        self.assertEqual(len(invoices), 3)
        # ordering is by year then id
        self.assertEqual([i.year for i in invoices], [2015, 2016, 2020])

    def test_get_by_number(self):
        """
        Test the get_by_number method, including per-year scoping
        """
        self.assertEqual(
            DuesInvoiceRepository.get_by_number(2348, 2015).invoice_no, 2348)
        self.assertEqual(
            DuesInvoiceRepository.get_by_number(9878, 2018).invoice_no, 9878)
        # number exists only for its year
        self.assertIsNone(DuesInvoiceRepository.get_by_number(2348, 2016))
        self.assertIsNone(DuesInvoiceRepository.get_by_number(1234, 2000))

    def test_get_by_membership_number(self):
        """
        Test the get_by_membership_number method
        """
        self.assertEqual(
            len(DuesInvoiceRepository.get_by_membership_number(9, [2000])), 0)
        self.assertEqual(
            len(DuesInvoiceRepository.get_by_membership_number(9, [2018])), 3)
        self.assertEqual(
            len(DuesInvoiceRepository.get_by_membership_number(9)), 8)
        self.assertEqual(
            len(DuesInvoiceRepository.get_by_membership_number(
                9, [2018, 2019, 2020])), 5)

    def test_get_max_invoice_number(self):
        """
        Test the get_max_invoice_number method
        """
        self.assertEqual(DuesInvoiceRepository.get_max_invoice_number(2000), 0)
        self.assertEqual(DuesInvoiceRepository.get_max_invoice_number(2015),
                         2348)
        self.assertEqual(DuesInvoiceRepository.get_max_invoice_number(2018),
                         9878)
        self.assertEqual(DuesInvoiceRepository.get_max_invoice_number(2020),
                         2020)

    def test_token_exists(self):
        """
        Test the token_exists method
        """
        self.assertTrue(
            DuesInvoiceRepository.token_exists('15WXYZ7890', 2015))
        self.assertTrue(
            DuesInvoiceRepository.token_exists('18WXYZ7890', 2018))
        # token does not exist for a not-configured year
        self.assertFalse(
            DuesInvoiceRepository.token_exists('15WXYZ7890', 2000))
        # token exists, but for a different year
        self.assertFalse(
            DuesInvoiceRepository.token_exists('15WXYZ7890', 2016))

    def test_get_monthly_stats(self):
        """
        Test the get_monthly_stats method

        Invoices come from the dues_invoices table, payments from the dues
        accounts.
        """
        # 2015: one invoice and one payment in the same month
        stats = DuesInvoiceRepository.get_monthly_stats(2015)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1, 0, 0))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'],
                               Decimal('9876.15'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[0]['amount_paid'], Decimal('15.11'))

        # 2018: invoice, reversal invoice and reduced invoice + payment
        stats = DuesInvoiceRepository.get_monthly_stats(2018)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2018, 1, 1, 0, 0))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'],
                               Decimal('9876.18'))
        self.assertEqual(stats[1]['month'], datetime(2018, 9, 1, 0, 0))
        self.assertAlmostEqual(stats[1]['amount_invoiced_normal'],
                               Decimal('5678.18'))
        self.assertAlmostEqual(stats[1]['amount_invoiced_reversal'],
                               Decimal('-9876.18'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('18.11'))

        # a year without any data yields an empty result
        self.assertEqual(DuesInvoiceRepository.get_monthly_stats(2000), [])

    def test_create_dues_invoice(self):
        """
        Test the create_dues_invoice method writes invoice and dues account
        """
        member = C3sMember.get_by_id(1)
        invoice = DuesInvoiceRepository.create_dues_invoice(
            2021, member, 42, 'C3S-dues2021-0042', Decimal('50.0'), 'TOKEN42XYZ')
        self.assertEqual(invoice.year, 2021)
        self.assertEqual(invoice.invoice_no, 42)
        self.assertEqual(invoice.token, 'TOKEN42XYZ')

        persisted = DuesInvoiceRepository.get_by_number(42, 2021)
        self.assertEqual(persisted.invoice_no_string, 'C3S-dues2021-0042')

        # the member's dues account is updated
        dues = member.get_dues(2021)
        self.assertEqual(dues.invoice_no, 42)
        self.assertEqual(dues.token, 'TOKEN42XYZ')

    def test_store_dues(self):
        """
        Test the store_dues method stores amount and start on the account
        """
        member = C3sMember.get_by_id(1)
        DuesInvoiceRepository.store_dues(
            2021, member, DuesCalculation(Decimal('37.5'), 'q2_2021'))
        dues = member.get_dues(2021)
        self.assertEqual(dues.amount, Decimal('37.5'))
        self.assertEqual(dues.start, 'q2_2021')
        self.assertEqual(dues.balance, Decimal('37.5'))

    def test_record_dues_email_sent(self):
        """
        Test the record_dues_email_sent method
        """
        member = C3sMember.get_by_id(1)
        dues = member.get_dues(2021)
        self.assertFalse(dues.invoice)

        DuesInvoiceRepository.record_dues_email_sent(2021, member)

        self.assertTrue(member.get_dues(2021).invoice)
        self.assertEqual(
            member.get_dues(2021).invoice_date.date(), date.today())
