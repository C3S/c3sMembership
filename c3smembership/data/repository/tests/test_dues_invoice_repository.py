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
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice
from c3smembership.data.model.base.dues19invoice import Dues19Invoice
from c3smembership.data.model.base.dues20invoice import Dues20Invoice
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository


class TestDuesInvoiceRepository(unittest.TestCase):
    """
    Tests the DuesInvoiceRepository class
    """

    def setUp(self):
        """
        Set up test cases
        """
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'member1@example.com',
                address1=u'addr one',
                address2=u'addr two',
                postcode=u'12345',
                city=u'Footown Mäh',
                country=u'Foocountry',
                locale=u'DE',
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u'GEMA',
                num_shares=35,
            )
            member1.membership_number = 9
            member1.membership_date = date(2018, 1, 1)
            member1.membership_accepted = True
            member1.dues15_paid_date = date(2015, 10, 31)
            member1.dues15_amount_paid = Decimal('15.11')
            member1.dues16_paid_date = date(2016, 12, 31)
            member1.dues16_amount_paid = Decimal('16.11')
            member1.dues17_paid_date = date(2017, 11, 30)
            member1.dues17_amount_paid = Decimal('17.11')
            member1.dues18_paid_date = date(2018, 9, 30)
            member1.dues18_amount_paid = Decimal('18.11')
            member1.dues19_paid_date = date(2019, 11, 19)
            member1.dues19_amount_paid = Decimal('19.11')
            member1.dues20_paid_date = date(2020, 11, 20)
            member1.dues20_amount_paid = Decimal('20.11')
            self.db_session.add(member1)
            self.db_session.flush()
            self.db_session.add(Dues15Invoice(
                invoice_no=2348,
                invoice_no_string=u'dues15-2348',
                invoice_date=date(2015, 10, 1),
                invoice_amount=Decimal('9876.15'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'15KVNM9265'))
            self.db_session.add(Dues16Invoice(
                invoice_no=1276,
                invoice_no_string=u'dues16-1276',
                invoice_date=date(2016, 6, 16),
                invoice_amount=Decimal('9876.16'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'16LLPW2254'))
            self.db_session.add(Dues17Invoice(
                invoice_no=7544,
                invoice_no_string=u'dues17-7544',
                invoice_date=date(2017, 7, 17),
                invoice_amount=Decimal('9876.17'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'17WEDD8349'))
            dues18invoice_original = Dues18Invoice(
                invoice_no=9876,
                invoice_no_string=u'dues18-9876',
                invoice_date=date(2018, 1, 12),
                invoice_amount=Decimal('9876.18'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'18SNED2845')
            self.db_session.add(dues18invoice_original)
            dues18invoice_reversal = Dues18Invoice(
                invoice_no=9877,
                invoice_no_string=u'dues18-9877-S',
                invoice_date=date(2018, 9, 18),
                invoice_amount=Decimal('-9876.18'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'18SNED2846')
            self.db_session.add(dues18invoice_reversal)

            dues18invoice_original.is_cancelled = True
            dues18invoice_original.cancelled_date = date(2018, 9, 18)
            dues18invoice_original.succeeding_invoice_no = '18SNED2846'

            dues18invoice_reversal.is_reversal = True
            dues18invoice_reversal.succeeding_invoice_no = '18SNED2847'

            dues18invoice_reduced = Dues18Invoice(
                invoice_no=9878,
                invoice_no_string=u'dues18-5678',
                invoice_date=date(2018, 9, 18),
                invoice_amount=Decimal('5678.18'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'18SNED2847')
            dues18invoice_reversal.preceding_invoice_no = '18SNED2846'
            dues18invoice_reduced.is_altered = True

            self.db_session.add(dues18invoice_reduced)
            self.db_session.add(Dues19Invoice(
                invoice_no=1234,
                invoice_no_string=u'dues19-1234',
                invoice_date=date(2019, 2, 24),
                invoice_amount=Decimal('1234.19'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'19WXYZ7890'))
            self.db_session.add(Dues20Invoice(
                invoice_no=2020,
                invoice_no_string=u'dues20-1234',
                invoice_date=date(2020, 2, 24),
                invoice_amount=Decimal('1234.20'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'20WXYZ7890'))

    def tearDown(self):
        """
        Tear down the set setup
        """
        self.db_session.close()
        DBSession.remove()

    def test_get_all(self):
        """
        Test the get_all method
        """
        invoices = DuesInvoiceRepository.get_all()
        self.assertEqual(len(invoices), 8)

        invoices = DuesInvoiceRepository.get_all([])
        self.assertEqual(len(invoices), 0)

        invoices = DuesInvoiceRepository.get_all([2015])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 2348)

        invoices = DuesInvoiceRepository.get_all([2016])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 1276)

        invoices = DuesInvoiceRepository.get_all([2017])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 7544)

        invoices = DuesInvoiceRepository.get_all([2018])
        self.assertEqual(len(invoices), 3)
        self.assertEqual(invoices[0].invoice_no, 9876)
        self.assertEqual(invoices[1].invoice_no, 9877)
        self.assertEqual(invoices[2].invoice_no, 9878)

        invoices = DuesInvoiceRepository.get_all([2019])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 1234)

        invoices = DuesInvoiceRepository.get_all([2020])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 2020)

        invoices = DuesInvoiceRepository.get_all([
            2015, 2016, 2017, 2018, 2019, 2020])
        self.assertEqual(len(invoices), 8)
        self.assertEqual(invoices[0].invoice_no, 2348)
        self.assertEqual(invoices[1].invoice_no, 1276)
        self.assertEqual(invoices[2].invoice_no, 7544)
        self.assertEqual(invoices[3].invoice_no, 9876)
        self.assertEqual(invoices[4].invoice_no, 9877)
        self.assertEqual(invoices[5].invoice_no, 9878)
        self.assertEqual(invoices[6].invoice_no, 1234)
        self.assertEqual(invoices[7].invoice_no, 2020)

    def test_get_by_number(self):
        """
        Test the get_by_number method
        """
        invoice = DuesInvoiceRepository.get_by_number(2348, 2015)
        self.assertEqual(invoice.invoice_no, 2348)

        invoice = DuesInvoiceRepository.get_by_number(1276, 2016)
        self.assertEqual(invoice.invoice_no, 1276)

        invoice = DuesInvoiceRepository.get_by_number(7544, 2017)
        self.assertEqual(invoice.invoice_no, 7544)

        invoice = DuesInvoiceRepository.get_by_number(9876, 2018)
        self.assertEqual(invoice.invoice_no, 9876)
        invoice = DuesInvoiceRepository.get_by_number(9877, 2018)
        self.assertEqual(invoice.invoice_no, 9877)
        invoice = DuesInvoiceRepository.get_by_number(9878, 2018)
        self.assertEqual(invoice.invoice_no, 9878)

        invoice = DuesInvoiceRepository.get_by_number(1234, 2019)
        self.assertEqual(invoice.invoice_no, 1234)

        invoice = DuesInvoiceRepository.get_by_number(2020, 2020)
        self.assertEqual(invoice.invoice_no, 2020)

        invoice = DuesInvoiceRepository.get_by_number(1234, 2000)
        self.assertIsNone(invoice)

    def test_get_by_membership_number(self):
        """
        Test the get_by_membership_number method
        """
        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2000])
        self.assertEqual(len(invoices), 0)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2015])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2016])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2017])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2018])
        self.assertEqual(len(invoices), 3)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2019])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2020])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2018, 2019, 2020])
        self.assertEqual(len(invoices), 5)
        self.assertEqual(invoices[0].invoice_no, 9876)
        self.assertEqual(invoices[1].invoice_no, 9877)
        self.assertEqual(invoices[2].invoice_no, 9878)
        self.assertEqual(invoices[3].invoice_no, 1234)
        self.assertEqual(invoices[4].invoice_no, 2020)

        invoices = DuesInvoiceRepository.get_by_membership_number(9)
        self.assertEqual(len(invoices), 8)

    def test_get_max_invoice_number(self):
        """
        Test the get_max_invoice_number method
        """
        max_number = DuesInvoiceRepository.get_max_invoice_number(2000)
        self.assertEqual(max_number, 0)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2015)
        self.assertEqual(max_number, 2348)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2016)
        self.assertEqual(max_number, 1276)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2017)
        self.assertEqual(max_number, 7544)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2018)
        self.assertEqual(max_number, 9878)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2019)
        self.assertEqual(max_number, 1234)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2020)
        self.assertEqual(max_number, 2020)

        max_number = DuesInvoiceRepository.get_max_invoice_number(None)
        self.assertEqual(max_number, 0)

    def test_token_exists(self):
        """
        Test the token_exists method

        1. Check existing tokens
        2. Check token for not existing year
        3. Check existing token for different year
        """
        # 1. Check existing tokens
        token_exists = DuesInvoiceRepository.token_exists(u'15KVNM9265', 2015)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'16LLPW2254', 2016)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'17WEDD8349', 2017)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'18SNED2845', 2018)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'18SNED2846', 2018)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'18SNED2847', 2018)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'19WXYZ7890', 2019)
        self.assertTrue(token_exists)

        token_exists = DuesInvoiceRepository.token_exists(u'20WXYZ7890', 2020)
        self.assertTrue(token_exists)

        # 2. Check token for not existing year
        token_exists = DuesInvoiceRepository.token_exists(u'19WXYZ7890', 2000)
        self.assertFalse(token_exists)

        # 3. Check existing token for different year
        token_exists = DuesInvoiceRepository.token_exists(u'19WXYZ7890', 2015)
        self.assertFalse(token_exists)

    def test_get_monthly_stats(self):
        """
        Test the get_monthly_stats method

        1. Test 2015 with one invoice and one payment in the same month
        2. Test 2016 with one invoice and one payment with the payment in
           another month
        3. Test 2017 with one invoice and one payment with the payment in
           another month
        4. Test 2018 with invoice, reversal invoice and reduced invoice
        5. Test 2019 with one invoice and one payment with the payment in
           another month
        6. Test 2020 with one invoice and one payment with the payment in
           another month
        7. Test not configured year 2000

        TODO: DatabaseDecimal should not have to be rounded. Still, the results
        of stats are like
        Decimal('9876.149999999999636202119290828704833984375') they it should
        be exactly Decimal('9876.15'). This might be caused by the aggregation
        in SQL but should not.
        """
        # 1. Test 2015 with one invoice and one payment in the same month
        stats = DuesInvoiceRepository.get_monthly_stats(2015)
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('9876.15'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[0]['amount_paid'], Decimal('15.11'))

        # 2. Test 2016 with one invoice and one payment with the payment in
        #    another month
        stats = DuesInvoiceRepository.get_monthly_stats(2016)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2016, 6, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('9876.16'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertEqual(stats[0]['amount_paid'], Decimal('0'))

        self.assertEqual(stats[1]['month'], datetime(2016, 12, 1, 0, 0))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_normal'],
            Decimal('0'))
        self.assertEqual(stats[1]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('16.11'))

        # 3. Test 2017 with one invoice and one payment with the payment in
        #    another month
        stats = DuesInvoiceRepository.get_monthly_stats(2017)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2017, 7, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('9876.17'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertEqual(stats[0]['amount_paid'], Decimal('0'))

        self.assertEqual(stats[1]['month'], datetime(2017, 11, 1, 0, 0))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_normal'],
            Decimal('0'))
        self.assertEqual(stats[1]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('17.11'))

        # 4. Test 2018 with invoice, reversal invoice and reduced invoice
        stats = DuesInvoiceRepository.get_monthly_stats(2018)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2018, 1, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('9876.18'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertEqual(stats[0]['amount_paid'], Decimal('0'))

        self.assertEqual(stats[1]['month'], datetime(2018, 9, 1, 0, 0))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_normal'],
            Decimal('5678.18'))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_reversal'], Decimal('-9876.18'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('18.11'))

        # 5. Test 2019 with one invoice and one payment with the payment in
        #    another month
        stats = DuesInvoiceRepository.get_monthly_stats(2019)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2019, 2, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('1234.19'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertEqual(stats[0]['amount_paid'], Decimal('0'))

        self.assertEqual(stats[1]['month'], datetime(2019, 11, 1, 0, 0))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_normal'],
            Decimal('0'))
        self.assertEqual(stats[1]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('19.11'))

        # 6. Test 2020 with one invoice and one payment with the payment in
        #    another month
        stats = DuesInvoiceRepository.get_monthly_stats(2020)
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2020, 2, 1, 0, 0))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_normal'],
            Decimal('1234.20'))
        self.assertEqual(stats[0]['amount_invoiced_reversal'], Decimal('0'))
        self.assertEqual(stats[0]['amount_paid'], Decimal('0'))

        self.assertEqual(stats[1]['month'], datetime(2020, 11, 1, 0, 0))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_normal'],
            Decimal('0'))
        self.assertEqual(stats[1]['amount_invoiced_reversal'], Decimal('0'))
        self.assertAlmostEqual(stats[1]['amount_paid'], Decimal('20.11'))

        # 7. Test not configured year 2000
        stats = DuesInvoiceRepository.get_monthly_stats(2000)
        self.assertIsNone(stats)
