# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.payment_repository package.
"""

from datetime import date
from decimal import Decimal
import unittest

from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.models import C3sMember
from c3smembership.data.repository.payment_repository import PaymentRepository


class TestPaymentRepository(unittest.TestCase):
    """
    Tests the PaymentRepository class.
    """

    # pylint: disable=too-many-arguments,too-many-locals
    @classmethod
    def _create_member(
            cls, membership_number, firstname, lastname, dues15_paid,
            dues15_payment_date, dues15_payment_token, dues15_payment_amount,
            dues16_paid, dues16_payment_date, dues16_payment_token,
            dues16_payment_amount, dues17_paid, dues17_payment_date,
            dues17_payment_token, dues17_payment_amount):
        member = C3sMember(
            firstname=firstname,
            lastname=lastname,
            email=u'',
            address1=u'',
            address2=u'',
            postcode=u'',
            city=u'',
            country=u'',
            locale=u'',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=unicode(membership_number),
            password=u'',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=1,
        )
        member.membership_number = membership_number
        member.dues15_paid = dues15_paid
        member.dues15_amount_paid = dues15_payment_amount
        member.dues15_paid_date = dues15_payment_date
        member.dues15_token = dues15_payment_token

        member.dues16_paid = dues16_paid
        member.dues16_amount_paid = dues16_payment_amount
        member.dues16_paid_date, = dues16_payment_date,
        member.dues16_token = dues16_payment_token

        member.dues17_paid = dues17_paid
        member.dues17_amount_paid = dues17_payment_amount
        member.dues17_paid_date = dues17_payment_date
        member.dues17_token = dues17_payment_token
        return member

    def setUp(self):
        """
        Set up the test data.

        The test set is:

        date       amount firstname lastname reference membership_number
        ========== ====== ========= ======== ========= =================
        2015-01-01 15.11  Jane      Smith    JANE      1
        2015-01-03 15.13  Cassandra Jones    CASSANDRA 3
        2016-02-01 16.21  Jane      Smith    SMI       1
        2016-02-02 16.22  John      Smith    JOHN      2
        2016-02-03 16.23  Cassandra Jones    JONES     3
        2017-03-01 17.31  Jane      Smith    TH        1
        2017-03-02 17.32  John      Smith    SMITH     2
        """
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            # pylint: disable=no-member
            DBSession.add(self._create_member(
                membership_number=1,
                firstname=u'Jane',
                lastname=u'Smith',
                dues15_paid=True,
                dues15_payment_date=date(2015, 1, 1),
                dues15_payment_token=u'JANE',
                dues15_payment_amount=Decimal('15.11'),
                dues16_paid=True,
                dues16_payment_date=date(2016, 2, 1),
                dues16_payment_token=u'SMI',
                dues16_payment_amount=Decimal('16.21'),
                dues17_paid=True,
                dues17_payment_date=date(2017, 3, 1),
                dues17_payment_token=u'TH',
                dues17_payment_amount=Decimal('17.31'),
            ))
            DBSession.add(self._create_member(
                membership_number=2,
                firstname=u'John',
                lastname=u'Smith',
                dues15_paid=False,
                dues15_payment_date=None,
                dues15_payment_token=None,
                dues15_payment_amount=None,
                dues16_paid=True,
                dues16_payment_date=date(2016, 2, 2),
                dues16_payment_token=u'JOHN',
                dues16_payment_amount=Decimal('16.22'),
                dues17_paid=True,
                dues17_payment_date=date(2017, 3, 2),
                dues17_payment_token=u'SMITH',
                dues17_payment_amount=Decimal('17.32'),
            ))
            DBSession.add(self._create_member(
                membership_number=3,
                firstname=u'Cassandra',
                lastname=u'Jones',
                dues15_paid=True,
                dues15_payment_date=date(2015, 1, 3),
                dues15_payment_token=u'CASSANDRA',
                dues15_payment_amount=Decimal('15.13'),
                dues16_paid=True,
                dues16_payment_date=date(2016, 2, 3),
                dues16_payment_token=u'JONES',
                dues16_payment_amount=Decimal('16.23'),
                dues17_paid=False,
                dues17_payment_date=None,
                dues17_payment_token=None,
                dues17_payment_amount=None,
            ))

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()

    def test_get_payments_default_sort(self):
        """
        Tests the get payments method.

        Test:

        1. Test total number of payments
        2. Test first payment for default sorting
        3. Test paging and 4th payment for default sorting
        4. Test 2nd records for default sorting
        5. Test 7th record for default sorting
        """

        # 1. Test total number of payments
        payments = PaymentRepository.get_payments(1, 100)
        self.assertEqual(len(payments), 7)

        # 2. Test first payment for default sorting
        payments = PaymentRepository.get_payments(1, 1)
        self.assertEqual(payments[0]['date'], date(2015, 1, 1))
        self.assertEqual(payments[0]['account'], u'Membership dues 2015')
        self.assertEqual(payments[0]['reference'], u'JANE')
        self.assertEqual(payments[0]['membership_number'], 1)
        self.assertEqual(payments[0]['firstname'], u'Jane')
        self.assertEqual(payments[0]['lastname'], u'Smith')
        self.assertEqual(payments[0]['amount'], Decimal('15.11'))

        # 3. Test paging and 4th payment for default sorting
        payments = PaymentRepository.get_payments(2, 3)
        self.assertEqual(len(payments), 3)
        self.assertEqual(payments[0]['date'], date(2016, 2, 2))
        self.assertEqual(payments[0]['account'], u'Membership dues 2016')
        self.assertEqual(payments[0]['reference'], u'JOHN')
        self.assertEqual(payments[0]['membership_number'], 2)
        self.assertEqual(payments[0]['firstname'], u'John')
        self.assertEqual(payments[0]['lastname'], u'Smith')
        self.assertEqual(payments[0]['amount'], Decimal('16.22'))

        # 4. Test 2nd records for default sorting
        payments = PaymentRepository.get_payments(2, 1)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]['date'], date(2015, 1, 3))
        self.assertEqual(payments[0]['account'], u'Membership dues 2015')
        self.assertEqual(payments[0]['reference'], u'CASSANDRA')
        self.assertEqual(payments[0]['membership_number'], 3)
        self.assertEqual(payments[0]['firstname'], u'Cassandra')
        self.assertEqual(payments[0]['lastname'], u'Jones')
        self.assertEqual(payments[0]['amount'], Decimal('15.13'))

        # 5. Test 7th record for default sorting
        payments = PaymentRepository.get_payments(7, 1)
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]['date'], date(2017, 3, 2))
        self.assertEqual(payments[0]['account'], u'Membership dues 2017')
        self.assertEqual(payments[0]['reference'], u'SMITH')
        self.assertEqual(payments[0]['membership_number'], 2)
        self.assertEqual(payments[0]['firstname'], u'John')
        self.assertEqual(payments[0]['lastname'], u'Smith')
        self.assertEqual(payments[0]['amount'], Decimal('17.32'))

    def test_get_payments_filtering(self):
        """
        Tests the get payments method.

        The test set is:

        date       amount firstname lastname reference membership_number
        ========== ====== ========= ======== ========= =================
        2015-01-01 15.11  Jane      Smith    JANE      1
        2015-01-03 15.13  Cassandra Jones    CASSANDRA 3
        2016-02-01 16.21  Jane      Smith    SMI       1
        2016-02-02 16.22  John      Smith    JOHN      2
        2016-02-03 16.23  Cassandra Jones    JONES     3
        2017-03-01 17.31  Jane      Smith    TH        1
        2017-03-02 17.32  John      Smith    SMITH     2
        """
        payments = PaymentRepository.get_payments(
            1, 100, from_date=date(2016, 1, 31), to_date=date(2017, 3, 1))
        self.assertEqual(len(payments), 4)

        payments = PaymentRepository.get_payments(
            1, 100, from_date=date(2016, 2, 1), to_date=date(2017, 3, 1))
        self.assertEqual(len(payments), 4)

        payments = PaymentRepository.get_payments(
            1, 100, from_date=date(2016, 2, 2), to_date=date(2017, 3, 1))
        self.assertEqual(len(payments), 3)

        payments = PaymentRepository.get_payments(
            1, 100, from_date=date(2016, 2, 2), to_date=date(2017, 3, 5))
        self.assertEqual(len(payments), 4)

        # Test only from date without to date
        payments = PaymentRepository.get_payments(
            1, 100, from_date=date(2016, 2, 2))
        self.assertEqual(len(payments), 4)

        # Test only to date without from date
        payments = PaymentRepository.get_payments(
            1, 100, to_date=date(2017, 3, 1))
        self.assertEqual(len(payments), 6)

    def test_get_payments_sorting(self):
        """
        Tests the get payments method.

        The test set is:

        date       amount firstname lastname reference membership_number
        ========== ====== ========= ======== ========= =================
        2015-01-01 15.11  Jane      Smith    JANE      1
        2015-01-03 15.13  Cassandra Jones    CASSANDRA 3
        2016-02-01 16.21  Jane      Smith    SMI       1
        2016-02-02 16.22  John      Smith    JOHN      2
        2016-02-03 16.23  Cassandra Jones    JONES     3
        2017-03-01 17.31  Jane      Smith    TH        1
        2017-03-02 17.32  John      Smith    SMITH     2

        Test:

        1. Test sort property
        2. Test sort direction
        """

        # 1. Test sort property
        payments = PaymentRepository.get_payments(
            1, 100, sort_property='membership_number')
        self.assertEqual(len(payments), 7)
        self.assertEqual(payments[0]['membership_number'], 1)
        self.assertEqual(payments[1]['membership_number'], 1)
        self.assertEqual(payments[2]['membership_number'], 1)
        self.assertEqual(payments[3]['membership_number'], 2)
        self.assertEqual(payments[4]['membership_number'], 2)
        self.assertEqual(payments[5]['membership_number'], 3)
        self.assertEqual(payments[5]['membership_number'], 3)

        payments = PaymentRepository.get_payments(
            1, 100, sort_property='firstname')
        self.assertEqual(len(payments), 7)
        self.assertEqual(payments[0]['firstname'], 'Cassandra')
        self.assertEqual(payments[1]['firstname'], 'Cassandra')
        self.assertEqual(payments[2]['firstname'], 'Jane')
        self.assertEqual(payments[3]['firstname'], 'Jane')
        self.assertEqual(payments[4]['firstname'], 'Jane')
        self.assertEqual(payments[5]['firstname'], 'John')
        self.assertEqual(payments[5]['firstname'], 'John')

        # 2. Test sort direction
        with self.assertRaises(ValueError):
            payments = PaymentRepository.get_payments(
                1, 100, sort_property='some_not_existing_property')
