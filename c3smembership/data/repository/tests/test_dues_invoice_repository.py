# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.dues_invoice_repository package.
"""

from datetime import date
from decimal import Decimal
import unittest

# import mock
from sqlalchemy import engine_from_config
import transaction

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
            self.db_session.add(Dues18Invoice(
                invoice_no=9876,
                invoice_no_string=u'dues18-9876',
                invoice_date=date(2018, 9, 17),
                invoice_amount=Decimal('9876.18'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'18SNED2845'))
            self.db_session.add(Dues18Invoice(
                invoice_no=5678,
                invoice_no_string=u'dues18-5678',
                invoice_date=date(2018, 1, 23),
                invoice_amount=Decimal('5678.18'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'18WDLW3874'))
            self.db_session.add(Dues19Invoice(
                invoice_no=1234,
                invoice_no_string=u'dues19-1234',
                invoice_date=date(2019, 2, 24),
                invoice_amount=Decimal('1234.19'),
                member_id=member1.id,
                membership_no=member1.membership_number,
                email=member1.email,
                token=u'19WXYZ7890'))

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
        self.assertEqual(len(invoices), 6)

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
        self.assertEqual(len(invoices), 2)
        self.assertEqual(invoices[0].invoice_no, 9876)
        self.assertEqual(invoices[1].invoice_no, 5678)

        invoices = DuesInvoiceRepository.get_all([2019])
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0].invoice_no, 1234)

        invoices = DuesInvoiceRepository.get_all([
            2015, 2016, 2017, 2018, 2019])
        self.assertEqual(len(invoices), 6)
        self.assertEqual(invoices[0].invoice_no, 2348)
        self.assertEqual(invoices[1].invoice_no, 1276)
        self.assertEqual(invoices[2].invoice_no, 7544)
        self.assertEqual(invoices[3].invoice_no, 9876)
        self.assertEqual(invoices[4].invoice_no, 5678)
        self.assertEqual(invoices[5].invoice_no, 1234)

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

        invoice = DuesInvoiceRepository.get_by_number(5678, 2018)
        self.assertEqual(invoice.invoice_no, 5678)

        invoice = DuesInvoiceRepository.get_by_number(1234, 2019)
        self.assertEqual(invoice.invoice_no, 1234)

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
        self.assertEqual(len(invoices), 2)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2019])
        self.assertEqual(len(invoices), 1)

        invoices = DuesInvoiceRepository.get_by_membership_number(
            9, [2018, 2019])
        self.assertEqual(len(invoices), 3)
        self.assertEqual(invoices[0].invoice_no, 9876)
        self.assertEqual(invoices[1].invoice_no, 5678)
        self.assertEqual(invoices[2].invoice_no, 1234)

        invoices = DuesInvoiceRepository.get_by_membership_number(9)
        self.assertEqual(len(invoices), 6)

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
        self.assertEqual(max_number, 9876)

        max_number = DuesInvoiceRepository.get_max_invoice_number(2019)
        self.assertEqual(max_number, 1234)

        max_number = DuesInvoiceRepository.get_max_invoice_number(None)
        self.assertEqual(max_number, 0)
