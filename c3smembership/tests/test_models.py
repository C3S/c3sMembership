# -*- coding: utf-8  -*-
from datetime import (
    date,
    datetime,
    timedelta,
)
from decimal import Decimal as D
from decimal import InvalidOperation
import unittest

from pyramid import testing
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
import transaction

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository

DEBUG = False


class C3sMembershipModelTestBase(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        self.session = DBSession()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        DBSession.remove()

    @classmethod
    def _get_target_class(cls):
        return C3sMember

    def _make_one(self,
                  firstname='SomeFirstnäme',
                  lastname='SomeLastnäme',
                  email='some@shri.de',
                  address1="addr one",
                  address2="addr two",
                  postcode="12345",
                  city="Footown Mäh",
                  country="Foocountry",
                  locale="DE",
                  date_of_birth=date.today(),
                  email_is_confirmed=False,
                  email_confirm_code='ABCDEFGHIK',
                  password='arandompassword',
                  date_of_submission=date.today(),
                  membership_type='normal',
                  member_of_colsoc=True,
                  name_of_colsoc="GEMA",
                  num_shares='23'):
        return self._get_target_class()(  # order of params DOES matter
            firstname, lastname, email,
            password,
            address1, address2, postcode,
            city, country, locale,
            date_of_birth, email_is_confirmed, email_confirm_code,
            num_shares,
            date_of_submission,
            membership_type,
            member_of_colsoc, name_of_colsoc,
        )

    def _make_another_one(self,
                          firstname='SomeFirstname',
                          lastname='SomeLastname',
                          email='some@shri.de',
                          address1="addr one",
                          address2="addr two",
                          postcode="12345",
                          city="Footown Muh",
                          country="Foocountry",
                          locale="DE",
                          date_of_birth=date.today(),
                          email_is_confirmed=False,
                          email_confirm_code='0987654321',
                          password='arandompassword',
                          date_of_submission=date.today(),
                          membership_type='investing',
                          member_of_colsoc=False,
                          name_of_colsoc="deletethis",
                          num_shares='23'):
        return self._get_target_class()(  # order of params DOES matter
            firstname, lastname, email,
            password,
            address1, address2, postcode,
            city, country, locale,
            date_of_birth, email_is_confirmed, email_confirm_code,
            num_shares,
            date_of_submission,
            membership_type, member_of_colsoc, name_of_colsoc,
        )


class C3sMembershipModelTests(C3sMembershipModelTestBase):

    def setUp(self):
        """
        prepare for tests: have one member in the database
        """
        super(C3sMembershipModelTests, self).setUp()
        with transaction.manager:
            member1 = C3sMember(  # german
                firstname='SomeFirstnäme',
                lastname='SomeLastnäme',
                email='some@shri.de',
                address1="addr one",
                address2="addr two",
                postcode="12345",
                city="Footown Mäh",
                country="Foocountry",
                locale="DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGFOO',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc="GEMA",
                num_shares='23',
            )
            self.session.add(member1)
            self.session.flush()

    def test_constructor(self):
        instance = self._make_one()
        self.assertEqual(instance.firstname, 'SomeFirstnäme', "No match!")
        self.assertEqual(instance.lastname, 'SomeLastnäme', "No match!")
        self.assertEqual(instance.email, 'some@shri.de', "No match!")
        self.assertEqual(instance.address1, 'addr one', "No match!")
        self.assertEqual(instance.address2, 'addr two', "No match!")
        self.assertEqual(instance.email, 'some@shri.de', "No match!")
        self.assertEqual(
            instance.email_confirm_code, 'ABCDEFGHIK', "No match!")
        self.assertEqual(instance.email_is_confirmed, False, "expected False")
        self.assertEqual(instance.membership_type, 'normal', "No match!")

    def test_get_password(self):
        """
        Test the _get_password function.
        """
        instance = self._make_one()
        self.assertEqual(instance.password, instance._password)

    def test_get_number(self):
        """
        test: get the number of entries in the database
        """
        instance = self._make_one()
        self.session.add(instance)
        self.assertEqual(self._get_target_class().get_number(), 2)

    # GET BY .. tests # # # # # # # # # # # # # # # # # # # # # # # # # # #
    def test_get_by_code(self):
        """
        test: get one entry by code
        """
        instance = self._make_one()
        self.session.add(instance)
        instance_from_db = self._get_target_class().get_by_code('ABCDEFGHIK')
        self.assertEqual(instance.firstname, 'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, 'some@shri.de')

    def test_get_by_email(self):
        """
        test: get one entry by email
        """
        instance = self._make_one()
        self.session.add(instance)
        list_from_db = self._get_target_class().get_by_email(
            'some@shri.de')
        self.assertEqual(list_from_db[0].firstname, 'SomeFirstnäme')
        self.assertEqual(list_from_db[0].email, 'some@shri.de')

    def test_get_by_id(self):
        """
        test: get one entry by id
        """
        instance = self._make_one()
        self.session.add(instance)
        self.session.flush()
        _id = instance.id
        _date_of_birth = instance.date_of_birth
        _date_of_submission = instance.date_of_submission
        instance_from_db = self._get_target_class().get_by_id(_id)
        self.assertEqual(instance_from_db.firstname, 'SomeFirstnäme')
        self.assertEqual(instance_from_db.lastname, 'SomeLastnäme')
        self.assertEqual(instance_from_db.email, 'some@shri.de')
        self.assertEqual(instance_from_db.address1, 'addr one')
        self.assertEqual(instance_from_db.address2, 'addr two')
        self.assertEqual(instance_from_db.postcode, '12345')
        self.assertEqual(instance_from_db.city, 'Footown Mäh')
        self.assertEqual(instance_from_db.country, 'Foocountry')
        self.assertEqual(instance_from_db.locale, 'DE')
        self.assertEqual(instance_from_db.date_of_birth, _date_of_birth)
        self.assertEqual(instance_from_db.email_is_confirmed, False)
        self.assertEqual(instance_from_db.email_confirm_code, 'ABCDEFGHIK')
        self.assertEqual(instance_from_db.date_of_submission,
                         _date_of_submission)
        self.assertEqual(instance_from_db.membership_type, 'normal')
        self.assertEqual(instance_from_db.member_of_colsoc, True)
        self.assertEqual(instance_from_db.name_of_colsoc, 'GEMA')
        self.assertEqual(instance_from_db.num_shares, '23')

    def test_get_all(self):
        """
        test: get all entries
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance, instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(len(my_membership_signee_class.get_all()), 2)

    def test_get_dues_invoicees(self):
        """
        test: get all members that haven't had their invoices sent for a year
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance)
        self.session.add(instance2)
        self.session.flush()
        cls = self._get_target_class()

        instance.membership_accepted = False
        instance.membership_date = None
        instance2.membership_accepted = False
        instance2.membership_date = None
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 0)

        # change details so they be found
        instance.membership_accepted = True
        instance.membership_date = date(2016, 12, 1)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)

        instance2.membership_accepted = True
        instance2.membership_date = date(2016, 12, 2)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 2)

        # test boundary cases for membership date with one instance
        self.session.delete(instance2)
        self.session.flush()
        instance.membership_date = date(2017, 1, 1)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)

        instance.membership_date = date(2017, 12, 31)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)

        instance.membership_date = date(2018, 1, 1)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 0)

        # test membership loss
        instance.membership_date = date(2016, 2, 3)
        instance.membership_loss_date = None
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)

        instance.membership_loss_date = date(2017, 1, 1)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)

        instance.membership_loss_date = date(2016, 12, 31)
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 0)

        # once the dues invoice has been sent the member is no invoicee anymore
        instance.membership_loss_date = None
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 1)
        dues = instance.get_dues(2017)
        dues.invoice = True
        self.session.flush()
        self.assertEqual(len(cls.get_dues_invoicees(2017, 27)), 0)

    def test_delete_by_id(self):
        """
        test: delete one entry by id
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        instance_from_db = my_membership_signee_class.get_by_id('1')
        my_membership_signee_class.delete_by_id('1')
        instance_from_db = my_membership_signee_class.get_by_id('1')
        self.assertEqual(None, instance_from_db)

    def test_check_user_or_none(self):
        """
        XXX TODO
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        # get first dataset (id = 1)
        members = my_membership_signee_class.check_user_or_none('1')
        self.assertEqual(1, members.id)
        # get invalid dataset
        result2 = my_membership_signee_class.check_user_or_none('1234567')
        self.assertEqual(None, result2)

    def test_existing_confirm_code(self):
        """
        XXX TODO
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()

        members = my_membership_signee_class.check_for_existing_confirm_code(
            'ABCDEFGHIK')
        self.assertEqual(members, True)
        result2 = my_membership_signee_class.check_for_existing_confirm_code(
            'ABCDEFGHIK0000000000')
        self.assertEqual(result2, False)

    def test_member_listing(self):
        """
        Test the member_listing classmethod in models.py
        """
        instance = self._make_one()
        self.session.add(instance)
        instance2 = self._make_another_one()
        self.session.add(instance2)
        my_membership_signee_class = self._get_target_class()

        members = my_membership_signee_class.member_listing("id")
        self.assertTrue(members[0].firstname == "SomeFirstnäme")
        self.assertTrue(members[1].firstname == "SomeFirstnäme")
        self.assertTrue(members[2].firstname == "SomeFirstname")
        self.assertEqual(len(members.all()), 3)

    def test_member_listing_exception(self):
        """
        XXX TODO
        """
        instance = self._make_one()
        self.session.add(instance)
        instance2 = self._make_another_one()
        self.session.add(instance2)
        my_membership_signee_class = self._get_target_class()

        with self.assertRaises(Exception):
            members = my_membership_signee_class.member_listing("foo")

    def test_nonmember_listing(self):
        """
        Test the nonmember_listing classmethod in models.py
        """
        instance = self._make_one()
        self.session.add(instance)
        instance2 = self._make_another_one()
        self.session.add(instance2)
        my_membership_signee_class = self._get_target_class()

        # try order_by with faulty expression -- must raise
        with self.assertRaises(Exception):
            members = my_membership_signee_class.nonmember_listing(
                0, 100, 'schmoo')
        # try order with faulty expression -- must raise
        with self.assertRaises(Exception):
            members = my_membership_signee_class.nonmember_listing(
                0, 100, 'id', 'schmoo')
        members = my_membership_signee_class.nonmember_listing(
            0, 100, 'id')
        self.assertTrue(members[0].firstname == 'SomeFirstnäme')
        self.assertTrue(members[1].firstname == 'SomeFirstnäme')
        self.assertTrue(members[2].firstname == 'SomeFirstname')
        for member in members:
            self.assertTrue(not member.membership_accepted)
        members = my_membership_signee_class.nonmember_listing(
            0, 100, 'id', 'desc')
        self.assertTrue(members[0].firstname == 'SomeFirstname')
        self.assertTrue(members[1].firstname == 'SomeFirstnäme')
        self.assertTrue(members[2].firstname == 'SomeFirstnäme')
        for member in members:
            self.assertTrue(not member.membership_accepted)

    def test_nonmember_listing_count(self):
        """
        Test the nonmember_listing_count classmethod in models.py
        """
        instance = self._make_one()
        self.session.add(instance)
        instance2 = self._make_another_one()
        self.session.add(instance2)
        my_membership_signee_class = self._get_target_class()

        # try order with faulty expression -- must raise
        with self.assertRaises(Exception):
            members = my_membership_signee_class.nonmember_listing(
                0, 100, 'id', 'schmoo')
        members = my_membership_signee_class.nonmember_listing(
            0, 100, 'id')
        self.assertTrue(members[0].firstname == 'SomeFirstnäme')
        self.assertTrue(members[1].firstname == 'SomeFirstnäme')
        self.assertTrue(members[2].firstname == 'SomeFirstname')
        result2 = my_membership_signee_class.nonmember_listing(
            0, 100, 'id', 'desc')
        self.assertTrue(result2[0].firstname == 'SomeFirstname')
        self.assertTrue(result2[1].firstname == 'SomeFirstnäme')
        self.assertTrue(result2[2].firstname == 'SomeFirstnäme')

    def test_get_num_members_accepted(self):
        """
        test: get the number of accepted member entries in the database
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(
            my_membership_signee_class.get_num_members_accepted(),
            0)
        # go again
        instance.membership_accepted = True
        self.assertEqual(
            my_membership_signee_class.get_num_members_accepted(),
            1)

    def test_get_num_non_accepted(self):
        """
        test: get the number of non-accepted member entries in the database
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(my_membership_signee_class.get_num_non_accepted(), 2)
        # go again
        instance.membership_accepted = True
        self.assertEqual(my_membership_signee_class.get_num_non_accepted(), 1)

    def test_get_num_mem_nat_acc(self):
        """
        test: get the number of accepted member entries being natural persons
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(my_membership_signee_class.get_num_mem_nat_acc(), 0)
        # go again
        instance.membership_accepted = True
        self.assertEqual(my_membership_signee_class.get_num_mem_nat_acc(), 1)

    def test_get_num_mem_jur_acc(self):
        """
        test: get the number of accepted member entries being legal entities
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(my_membership_signee_class.get_num_mem_jur_acc(), 0)
        # go again
        instance.membership_accepted = True
        instance.is_legalentity = True
        self.assertEqual(my_membership_signee_class.get_num_mem_jur_acc(), 1)

    def test_get_num_mem_norm(self):
        """
        test: get the number of accepted member entries being normal members.
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        self.assertEqual(my_membership_signee_class.get_num_mem_norm(), 0)
        # go again
        instance.membership_accepted = True
        self.assertEqual(instance.membership_type, 'normal')
        self.assertEqual(my_membership_signee_class.get_num_mem_norm(), 1)

    def test_get_num_mem_invest(self):
        """
        test: get the number of accepted member entries being investing members
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        number_from_db = my_membership_signee_class.get_num_mem_invest()
        self.assertEqual(number_from_db, 0)
        # go again
        instance.membership_accepted = True
        instance.membership_type = 'investing'
        self.assertEqual(instance.membership_type, 'investing')
        number_from_db = my_membership_signee_class.get_num_mem_invest()
        self.assertEqual(number_from_db, 1)

    def test_get_num_mem_other_features(self):
        """
        test: get number of accepted member entries with silly membership type
        """
        instance = self._make_one()
        self.session.add(instance)
        my_membership_signee_class = self._get_target_class()
        number_from_db = my_membership_signee_class.get_num_mem_other_features()
        self.assertEqual(number_from_db, 0)
        # go again
        instance.membership_accepted = True
        instance.membership_type = 'pondering'
        self.assertEqual(instance.membership_type, 'pondering')
        number_from_db = my_membership_signee_class.get_num_mem_other_features()
        self.assertEqual(number_from_db, 1)

    def test_is_member(self):
        member = C3sMember(  # german
            firstname='SomeFirstnäme',
            lastname='SomeLastnäme',
            email='some@shri.de',
            address1="addr one",
            address2="addr two",
            postcode="12345",
            city="Footown Mäh",
            country="Foocountry",
            locale="DE",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='ABCDEFGFOO',
            password='arandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc="GEMA",
            num_shares='23',
        )

        # not member
        member.membership_accepted = False
        member.membership_loss_date = None
        self.assertEqual(member.is_member(), False)

        # Accepted after check date
        member.membership_accepted = True
        member.membership_date = date(2016, 1, 1)
        member.membership_loss_date = None
        self.assertEqual(member.is_member(date(2015, 12, 31)), False)

        # Accepted in the past
        member.membership_accepted = True
        member.membership_date = date(2016, 1, 1)
        member.membership_loss_date = None
        self.assertEqual(member.is_member(), True)

        # If loss date is today then the member still has membership until the
        # end of the day
        member.membership_accepted = True
        member.membership_date = date(2016, 1, 1)
        member.membership_loss_date = date.today()
        self.assertEqual(member.is_member(), True)

        # If the loss date is in the future then the member still has
        # membership
        member.membership_accepted = True
        member.membership_date = date(2016, 1, 1)
        member.membership_loss_date = date.today() + timedelta(days=1)
        self.assertEqual(member.is_member(), True)

        # If the loss date is in the past then the member no longer has
        # membership
        member.membership_accepted = True
        member.membership_date = date(2016, 1, 1)
        member.membership_loss_date = date.today() - timedelta(days=1)
        self.assertEqual(member.is_member(), False)


class TestMemberListing(C3sMembershipModelTestBase):
    def setUp(self):
        super(TestMemberListing, self).setUp()
        instance = self._make_one(
            lastname="ABC",
            firstname='xyz',
            email_confirm_code='0987654321')
        self.session.add(instance)
        instance = self._make_another_one(
            lastname="DEF",
            firstname='abc',
            email_confirm_code='19876543210')
        self.session.add(instance)
        instance = self._make_another_one(
            lastname="GHI",
            firstname='def',
            email_confirm_code='098765432101')
        self.session.add(instance)
        self.session.flush()
        self.class_under_test = self._get_target_class()

    def test_order_last_sort_last(self):
        result = self.class_under_test.member_listing(order_by='lastname')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].lastname)
        self.assertEqual("GHI", result[-1].lastname)

    def test_order_last_asc_sort_last(self):
        result = self.class_under_test.member_listing(
            order_by='lastname', order="asc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].lastname)
        self.assertEqual("GHI", result[-1].lastname)

    def test_order_last_desc_sort_last(self):
        result = self.class_under_test.member_listing(
            order_by='lastname', order="desc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("GHI", result[0].lastname)
        self.assertEqual("ABC", result[-1].lastname)

    def test_order_invalid(self):
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by='unknown', order="desc")
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by=None, order="desc")
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by="", order="desc")
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by='lastname', order="unknown")
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by='lastname', order="")
        self.assertRaises(Exception, self.class_under_test.member_listing,
                          order_by='lastname', order=None)


class GroupTests(unittest.TestCase):
    """
    test the groups
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        self.session = DBSession()
        Base.metadata.create_all(engine)

        with transaction.manager:
            group1 = Group(name='staff')
            self.session.add(group1)
            self.session.flush()
            self.assertEqual(group1.__str__(), 'group:staff')

    def tearDown(self):
        self.session.close()
        DBSession.remove()

    def test_group(self):
        result = Group.get_staffers_group()
        self.assertEqual(result.__str__(), 'group:staff')

    def test__str__(self):
        staffers_group = Group.get_staffers_group()
        res = staffers_group.__str__()
        self.assertEqual(res, 'group:staff')


class StaffTests(unittest.TestCase):
    """
    test the staff and cashiers accounts
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        self.session = DBSession()
        Base.metadata.create_all(engine)

        with transaction.manager:
            group1 = Group(name='staff')
            group2 = Group(name='staff2')
            DBSession.add(group1, group2)
            DBSession.flush()

    def tearDown(self):
        self.session.close()
        DBSession.remove()

    def test_staff(self):
        staffer1 = Staff(
            login='staffer1',
            password='stafferspassword'
        )
        staffer1.group = ['staff']
        staffer2 = Staff(
            login='staffer2',
            password='staffer2spassword',
        )
        staffer2.group = ['staff2']

        self.session.add(staffer1)
        self.session.add(staffer2)
        self.session.flush()

        _staffer2_id = staffer2.id
        _staffer1_id = staffer1.id

        self.assertTrue(staffer2.password != '')

        self.assertEqual(
            Staff.get_by_id(_staffer1_id),
            Staff.get_by_login('staffer1')
        )
        self.assertEqual(
            Staff.get_by_id(_staffer2_id),
            Staff.get_by_login('staffer2')
        )

        # test get_all
        res = Staff.get_all()
        self.assertEqual(len(res), 2)

        # test delete_by_id
        Staff.delete_by_id(1)
        res = Staff.get_all()
        self.assertEqual(len(res), 1)

        # test check_user_or_none
        res1 = Staff.check_user_or_none('staffer2')
        res2 = Staff.check_user_or_none('staffer1')
        self.assertTrue(res1 is not None)
        self.assertTrue(res2 is None)

        # test check_password
        Staff.check_password('staffer2', 'staffer2spassword')

