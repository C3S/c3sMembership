# -*- coding: utf-8  -*-
# import os
from datetime import(
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
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


# Disable Pylint error message when using DBSession methods
# pylint: disable=no-member

DEBUG = False


class C3sMembershipModelTestBase(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_models.db')
        engine = create_engine('sqlite:///:memory:')
        self.session = DBSession
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_models.db')

    @classmethod
    def _get_target_class(cls):
        return C3sMember

    def _make_one(self,
                  firstname=u'SomeFirstnäme',
                  lastname=u'SomeLastnäme',
                  email=u'some@shri.de',
                  address1=u"addr one",
                  address2=u"addr two",
                  postcode=u"12345",
                  city=u"Footown Mäh",
                  country=u"Foocountry",
                  locale=u"DE",
                  date_of_birth=date.today(),
                  email_is_confirmed=False,
                  email_confirm_code=u'ABCDEFGHIK',
                  password=u'arandompassword',
                  date_of_submission=date.today(),
                  membership_type=u'normal',
                  member_of_colsoc=True,
                  name_of_colsoc=u"GEMA",
                  num_shares=u'23'):
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
                          firstname=u'SomeFirstname',
                          lastname=u'SomeLastname',
                          email=u'some@shri.de',
                          address1=u"addr one",
                          address2=u"addr two",
                          postcode=u"12345",
                          city=u"Footown Muh",
                          country=u"Foocountry",
                          locale=u"DE",
                          date_of_birth=date.today(),
                          email_is_confirmed=False,
                          email_confirm_code=u'0987654321',
                          password=u'arandompassword',
                          date_of_submission=date.today(),
                          membership_type=u'investing',
                          member_of_colsoc=False,
                          name_of_colsoc=u"deletethis",
                          num_shares=u'23'):
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
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)
            DBSession.flush()

    def test_constructor(self):
        instance = self._make_one()
        self.assertEqual(instance.firstname, u'SomeFirstnäme', "No match!")
        self.assertEqual(instance.lastname, u'SomeLastnäme', "No match!")
        self.assertEqual(instance.email, u'some@shri.de', "No match!")
        self.assertEqual(instance.address1, u'addr one', "No match!")
        self.assertEqual(instance.address2, u'addr two', "No match!")
        self.assertEqual(instance.email, u'some@shri.de', "No match!")
        self.assertEqual(
            instance.email_confirm_code, u'ABCDEFGHIK', "No match!")
        self.assertEqual(instance.email_is_confirmed, False, "expected False")
        self.assertEqual(instance.membership_type, u'normal', "No match!")

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
        instance_from_db = self._get_target_class().get_by_code(u'ABCDEFGHIK')
        self.assertEqual(instance.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')

    def test_get_by_dues15_token(self):
        """
        test: get one entry by token
        """
        instance = self._make_one()
        self.session.add(instance)
        instance.dues15_token = u'THIS_ONE'
        instance_from_db = self._get_target_class().get_by_dues15_token(
            u'THIS_ONE')
        self.assertEqual(instance_from_db.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')

    def test_get_by_dues16_token(self):
        """
        test: get one entry by token
        """
        instance = self._make_one()
        self.session.add(instance)
        instance.dues16_token = u'F73sjf29g4eEf9giJ'
        instance_from_db = self._get_target_class().get_by_dues16_token(
            u'F73sjf29g4eEf9giJ')
        self.assertEqual(instance_from_db.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')

    def test_get_by_dues17_token(self):
        """
        test: get one entry by token
        """
        instance = self._make_one()
        self.session.add(instance)
        instance.dues17_token = u'aa84f59a8fjf79oa83kd'
        instance_from_db = self._get_target_class().get_by_dues17_token(
            u'aa84f59a8fjf79oa83kd')
        self.assertEqual(instance_from_db.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')

    def test_get_by_dues18_token(self):
        """
        test: get one entry by token
        """
        instance = self._make_one()
        self.session.add(instance)
        instance.dues18_token = u'aa84f59a8fjf79oa83kd'
        instance_from_db = self._get_target_class().get_by_dues18_token(
            u'aa84f59a8fjf79oa83kd')
        self.assertEqual(instance_from_db.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')

    def test_get_by_email(self):
        """
        test: get one entry by email
        """
        instance = self._make_one()
        self.session.add(instance)
        list_from_db = self._get_target_class().get_by_email(
            u'some@shri.de')
        self.assertEqual(list_from_db[0].firstname, u'SomeFirstnäme')
        self.assertEqual(list_from_db[0].email, u'some@shri.de')

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
        self.assertEqual(instance_from_db.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_db.lastname, u'SomeLastnäme')
        self.assertEqual(instance_from_db.email, u'some@shri.de')
        self.assertEqual(instance_from_db.address1, u'addr one')
        self.assertEqual(instance_from_db.address2, u'addr two')
        self.assertEqual(instance_from_db.postcode, u'12345')
        self.assertEqual(instance_from_db.city, u'Footown Mäh')
        self.assertEqual(instance_from_db.country, u'Foocountry')
        self.assertEqual(instance_from_db.locale, u'DE')
        self.assertEqual(instance_from_db.date_of_birth, _date_of_birth)
        self.assertEqual(instance_from_db.email_is_confirmed, False)
        self.assertEqual(instance_from_db.email_confirm_code, u'ABCDEFGHIK')
        self.assertEqual(instance_from_db.date_of_submission,
                         _date_of_submission)
        self.assertEqual(instance_from_db.membership_type, u'normal')
        self.assertEqual(instance_from_db.member_of_colsoc, True)
        self.assertEqual(instance_from_db.name_of_colsoc, u'GEMA')
        self.assertEqual(instance_from_db.num_shares, u'23')

    def test_get_all(self):
        """
        test: get all entries
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance, instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()
        self.assertEquals(len(my_membership_signee_class.get_all()), 2)

    def test_get_dues15_invoicees(self):
        """
        test: get all members that haven't had their invoices sent
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance, instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()
        invoicees = my_membership_signee_class.get_dues15_invoicees(27)
        self.assertEquals(len(invoicees), 0)
        # change details so they be found
        instance.membership_accepted = True
        instance2.membership_accepted = True
        invoicees = my_membership_signee_class.get_dues15_invoicees(27)
        self.assertEquals(len(invoicees), 1)

    def test_get_dues16_invoicees(self):
        """
        test: get all members that haven't had their invoices sent
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance, instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()
        invoicees = my_membership_signee_class.get_dues16_invoicees(27)
        self.assertEquals(len(invoicees), 0)
        # change details so they be found
        instance.membership_accepted = True
        instance2.membership_accepted = True
        invoicees = my_membership_signee_class.get_dues16_invoicees(27)
        self.assertEquals(len(invoicees), 1)

    def test_get_dues17_invoicees(self):
        """
        test: get all members that haven't had their invoices sent
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance)
        self.session.add(instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()

        instance.membership_accepted = False
        instance.membership_date = None
        instance2.membership_accepted = False
        instance2.membership_date = None
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 0)

        # change details so they be found
        instance.membership_accepted = True
        instance.membership_date = date(2016, 12, 1)
        instance2.membership_accepted = False
        instance2.membership_date = None
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_accepted = True
        instance.membership_date = date(2016, 12, 1)
        instance2.membership_accepted = True
        instance2.membership_date = date(2016, 12, 2)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 2)

        # test boundary cases for membership date with one instance
        self.session.delete(instance2)
        self.session.flush()
        instance.membership_date = date(2017, 1, 1)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2017, 12, 31)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2016, 12, 31)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2018, 1, 1)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 0)

        # test membership loss
        instance.membership_date = date(2016, 2, 3)

        instance.membership_loss_date = None
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2018, 1, 1)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2017, 12, 31)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2017, 1, 1)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2016, 12, 31)
        invoicees = my_membership_signee_class.get_dues17_invoicees(27)
        self.assertEquals(len(invoicees), 0)

    def test_get_dues18_invoicees(self):
        """
        test: get all members that haven't had their invoices sent
        """
        instance = self._make_one()
        instance2 = self._make_another_one()
        self.session.add(instance)
        self.session.add(instance2)
        self.session.flush()
        my_membership_signee_class = self._get_target_class()

        instance.membership_accepted = False
        instance.membership_date = None
        instance2.membership_accepted = False
        instance2.membership_date = None
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 0)

        # change details so they be found
        instance.membership_accepted = True
        instance.membership_date = date(2017, 12, 1)
        instance2.membership_accepted = False
        instance2.membership_date = None
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_accepted = True
        instance.membership_date = date(2017, 12, 1)
        instance2.membership_accepted = True
        instance2.membership_date = date(2017, 12, 2)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 2)

        # test boundary cases for membership date with one instance
        self.session.delete(instance2)
        self.session.flush()
        instance.membership_date = date(2018, 1, 1)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2018, 12, 31)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2017, 12, 31)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_date = date(2019, 1, 1)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 0)

        # test membership loss
        instance.membership_date = date(2017, 2, 3)

        instance.membership_loss_date = None
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2019, 1, 1)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2018, 12, 31)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2018, 1, 1)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 1)

        instance.membership_loss_date = date(2017, 12, 31)
        invoicees = my_membership_signee_class.get_dues18_invoicees(27)
        self.assertEquals(len(invoicees), 0)

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
            u'ABCDEFGHIK')
        self.assertEqual(members, True)
        result2 = my_membership_signee_class.check_for_existing_confirm_code(
            u'ABCDEFGHIK0000000000')
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
        self.failUnless(members[0].firstname == u"SomeFirstnäme")
        self.failUnless(members[1].firstname == u"SomeFirstnäme")
        self.failUnless(members[2].firstname == u"SomeFirstname")
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
            if DEBUG:
                print members

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
        self.failUnless(members[0].firstname == u'SomeFirstnäme')
        self.failUnless(members[1].firstname == u'SomeFirstnäme')
        self.failUnless(members[2].firstname == u'SomeFirstname')
        for member in members:
            self.assertTrue(not member.membership_accepted)
        members = my_membership_signee_class.nonmember_listing(
            0, 100, 'id', 'desc')
        self.failUnless(members[0].firstname == u'SomeFirstname')
        self.failUnless(members[1].firstname == u'SomeFirstnäme')
        self.failUnless(members[2].firstname == u'SomeFirstnäme')
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
        self.failUnless(members[0].firstname == u'SomeFirstnäme')
        self.failUnless(members[1].firstname == u'SomeFirstnäme')
        self.failUnless(members[2].firstname == u'SomeFirstname')
        result2 = my_membership_signee_class.nonmember_listing(
            0, 100, 'id', 'desc')
        self.failUnless(result2[0].firstname == u'SomeFirstname')
        self.failUnless(result2[1].firstname == u'SomeFirstnäme')
        self.failUnless(result2[2].firstname == u'SomeFirstnäme')

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
        self.assertEqual(instance.membership_type, u'normal')
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
        instance.membership_type = u'investing'
        self.assertEqual(instance.membership_type, u'investing')
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
        instance.membership_type = u'pondering'
        self.assertEqual(instance.membership_type, u'pondering')
        number_from_db = my_membership_signee_class.get_num_mem_other_features()
        self.assertEqual(number_from_db, 1)

    def test_is_member(self):
        member = C3sMember(  # german
            firstname=u'SomeFirstnäme',
            lastname=u'SomeLastnäme',
            email=u'some@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"DE",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFGFOO',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'23',
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

        # If the loss date is in the future then the member still has membership
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
    """
    XXX TODO
    """
    def setUp(self):
        super(TestMemberListing, self).setUp()
        instance = self._make_one(
            lastname=u"ABC",
            firstname=u'xyz',
            email_confirm_code=u'0987654321')
        self.session.add(instance)
        instance = self._make_another_one(
            lastname=u"DEF",
            firstname=u'abc',
            email_confirm_code=u'19876543210')
        self.session.add(instance)
        instance = self._make_another_one(
            lastname=u"GHI",
            firstname=u'def',
            email_confirm_code=u'098765432101')
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
        self.assertRaises(self.class_under_test.member_listing,
                          order_by='unknown', order="desc")
        self.assertRaises(self.class_under_test.member_listing,
                          order_by=None, order="desc")
        self.assertRaises(self.class_under_test.member_listing,
                          order_by="", order="desc")
        self.assertRaises(self.class_under_test.member_listing,
                          order_by='lastname', order="unknown")
        self.assertRaises(self.class_under_test.member_listing,
                          order_by='lastname', order="")
        self.assertRaises(self.class_under_test.member_listing,
                          order_by='lastname', order=None)


class GroupTests(unittest.TestCase):
    """
    test the groups
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_groups.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            group1 = Group(name=u'staff')
            DBSession.add(group1)
            DBSession.flush()
            self.assertEquals(group1.__str__(), 'group:staff')

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_groups.db')

    def test_group(self):
        result = Group.get_staffers_group()
        self.assertEquals(result.__str__(), 'group:staff')

    def test__str__(self):
        staffers_group = Group.get_staffers_group()
        res = staffers_group.__str__()
        self.assertEquals(res, 'group:staff')


class StaffTests(unittest.TestCase):
    """
    test the staff and cashiers accounts
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_staff.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            group1 = Group(name=u'staff')
            group2 = Group(name=u'staff2')
            DBSession.add(group1, group2)
            DBSession.flush()

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_staff.db')

    def test_staff(self):
        staffer1 = Staff(
            login=u'staffer1',
            password=u'stafferspassword'
        )
        staffer1.group = ['staff']
        staffer2 = Staff(
            login=u'staffer2',
            password=u'staffer2spassword',
        )
        staffer2.group = ['staff2']

        self.session.add(staffer1)
        self.session.add(staffer2)
        self.session.flush()

        _staffer2_id = staffer2.id
        _staffer1_id = staffer1.id

        self.assertTrue(staffer2.password is not '')

        self.assertEqual(
            Staff.get_by_id(_staffer1_id),
            Staff.get_by_login(u'staffer1')
        )
        self.assertEqual(
            Staff.get_by_id(_staffer2_id),
            Staff.get_by_login(u'staffer2')
        )

        # test get_all
        res = Staff.get_all()
        self.assertEqual(len(res), 2)

        # test delete_by_id
        Staff.delete_by_id(1)
        res = Staff.get_all()
        self.assertEqual(len(res), 1)

        # test check_user_or_none
        res1 = Staff.check_user_or_none(u'staffer2')
        res2 = Staff.check_user_or_none(u'staffer1')
        self.assertTrue(res1 is not None)
        self.assertTrue(res2 is None)

        # test check_password
        Staff.check_password(u'staffer2', u'staffer2spassword')


class Dues15InvoiceModelTests(unittest.TestCase):
    """
    test the dues15 invoice model
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_staff.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)

            member2 = C3sMember(
                firstname=u'Franziska',
                lastname=u'Musterfrau',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO1',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member2)

            member3 = C3sMember(
                firstname=u'Jane',
                lastname=u'Somebody',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO2',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member3)

            dues1 = Dues15Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues15-0001',
                invoice_date=date(2015, 10, 01),
                invoice_amount=D('-37.50'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues1)

            dues2 = Dues15Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues15-0002-S',
                invoice_date=date(2015, 10, 02),
                invoice_amount=D('17.25'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'fa4wfjlasjfd',
            )
            dues2.is_reversal = True
            DBSession.add(dues2)

            dues3 = Dues15Invoice(
                invoice_no=3,
                invoice_no_string=u'C3S-dues15-0003',
                invoice_date=date(2015, 11, 25),
                invoice_amount=D('74.58'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'Jleifjsw9e',
            )
            DBSession.add(dues3)

            dues4 = Dues15Invoice(
                invoice_no=4,
                invoice_no_string=u'C3S-dues15-0004-S',
                invoice_date=date(2015, 11, 27),
                invoice_amount=D('23.85'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'f348h98sdf',
            )
            dues4.is_reversal = True
            DBSession.add(dues4)

            dues5 = Dues15Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues15-0005',
                invoice_date=date(2015, 11, 29),
                invoice_amount=D('12.89'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'sgdfoiddfg',
            )
            DBSession.add(dues5)

            dues6 = Dues15Invoice(
                invoice_no=6,
                invoice_no_string=u'C3S-dues15-0006-S',
                invoice_date=date(2015, 11, 30),
                invoice_amount=D('77.79'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'3o948n',
            )
            dues6.is_reversal = True
            DBSession.add(dues6)
            DBSession.flush()

            member1.set_dues15_payment(D('12.34'), date(2015, 10, 31))
            member2.set_dues15_payment(D('95.65'), date(2015, 11, 5))
            member3.set_dues15_payment(D('-85.12'), date(2015, 11, 30))

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_staff.db')

    def test_get_all(self):
        '''
        test get_all
        '''
        res = Dues15Invoice.get_all()
        self.assertEqual(len(res), 6)

    def test_get_by_invoice_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues15Invoice.get_by_invoice_no(1)
        self.assertEqual(res.id, 1)

    def test_get_by_membership_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues15Invoice.get_by_membership_no(1)
        self.assertEqual(res[0].id, 1)  # is a list

    def test_get_max_invoice_no(self):
        '''
        test get_max_invoice_no
        '''
        res = Dues15Invoice.get_max_invoice_no()
        self.assertEqual(res, 6)

    def test_existing_dues15_token(self):
        """
        test check_for_existing_dues15_token
        """
        res = Dues15Invoice.check_for_existing_dues15_token(
            u'ABCDEFGH')
        self.assertEqual(res, True)
        res2 = Dues15Invoice.check_for_existing_dues15_token(
            u'ABCDEFGHIK0000000000')
        self.assertEqual(res2, False)

    def test_get_monthly_stats(self):
        """
        Test get_monthly_stats.
        """
        stats = Dues15Invoice.get_monthly_stats()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'], D('-37.50'))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_reversal'], D('17.25'))
        self.assertAlmostEqual(stats[0]['amount_paid'], D('12.34'))
        self.assertEqual(stats[1]['month'], datetime(2015, 11, 1))
        self.assertAlmostEqual(stats[1]['amount_invoiced_normal'], D('87.47'))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_reversal'], D('101.64'))
        self.assertAlmostEqual(stats[1]['amount_paid'], D('10.53'))

    def test_decimality(self):
        """
        test the features of the 'amounts', esp. the format and persistence
        """

        # try to make another invoice with the same number
        def trigger_integrity_error_1():
            dues2 = Dues15Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues15-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_1)
        self.session.rollback()

        res = Dues15Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with the same string
        def trigger_integrity_error_2():
            dues2 = Dues15Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues15-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_2)
        self.session.rollback()

        res = Dues15Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with a non-decimal amount
        # InvalidOperation: Invalid literal for Decimal: '-37.50.20'
        def trigger_invalid_operation():
            dues2 = Dues15Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues15-0002',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50.20').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(InvalidOperation, trigger_invalid_operation)
        # trigger_invalid_operation()
        self.session.rollback()

        res = Dues15Invoice.get_all()
        self.assertEqual(len(res), 6)

        # now really store a new Dues15Invoice
        dues3 = Dues15Invoice(
            invoice_no=7,
            invoice_no_string=u'C3S-dues15-0002',
            invoice_date=date.today(),
            # invoice_amount=unicode(D('-37.50').to_eng_string()),
            invoice_amount=D('-37.50').to_eng_string(),
            member_id=1,
            membership_no=1,
            email=u'test@example.com',
            token=u'ABCDEFGH',
        )
        DBSession.add(dues3)
        DBSession.flush()

        res = Dues15Invoice.get_all()
        self.assertEqual(len(res), 7)
        self.assertEqual(dues3.id, 7)

class Dues16InvoiceModelTests(unittest.TestCase):
    """
    test the dues16 invoice model
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_staff.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)

            member2 = C3sMember(
                firstname=u'Franziska',
                lastname=u'Musterfrau',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO1',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member2)

            member3 = C3sMember(
                firstname=u'Jane',
                lastname=u'Somebody',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO2',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member3)

            dues1 = Dues16Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues16-0001',
                invoice_date=date(2015, 10, 01),
                invoice_amount=D('-37.50'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues1)

            dues2 = Dues16Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues16-0002-S',
                invoice_date=date(2015, 10, 02),
                invoice_amount=D('17.25'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'fa4wfjlasjfd',
            )
            dues2.is_reversal = True
            DBSession.add(dues2)

            dues3 = Dues16Invoice(
                invoice_no=3,
                invoice_no_string=u'C3S-dues16-0003',
                invoice_date=date(2015, 11, 25),
                invoice_amount=D('74.58'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'Jleifjsw9e',
            )
            DBSession.add(dues3)

            dues4 = Dues16Invoice(
                invoice_no=4,
                invoice_no_string=u'C3S-dues16-0004-S',
                invoice_date=date(2015, 11, 27),
                invoice_amount=D('23.85'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'f348h98sdf',
            )
            dues4.is_reversal = True
            DBSession.add(dues4)

            dues5 = Dues16Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues16-0005',
                invoice_date=date(2015, 11, 29),
                invoice_amount=D('12.89'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'sgdfoiddfg',
            )
            DBSession.add(dues5)

            dues6 = Dues16Invoice(
                invoice_no=6,
                invoice_no_string=u'C3S-dues16-0006-S',
                invoice_date=date(2015, 11, 30),
                invoice_amount=D('77.79'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'3o948n',
            )
            dues6.is_reversal = True
            DBSession.add(dues6)
            DBSession.flush()

            member1.set_dues16_payment(D('12.34'), date(2015, 10, 31))
            member2.set_dues16_payment(D('95.65'), date(2015, 11, 5))
            member3.set_dues16_payment(D('-85.12'), date(2015, 11, 30))

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_staff.db')

    def test_get_all(self):
        '''
        test get_all
        '''
        res = Dues16Invoice.get_all()
        self.assertEqual(len(res), 6)

    def test_get_by_invoice_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues16Invoice.get_by_invoice_no(1)
        self.assertEqual(res.id, 1)

    def test_get_by_membership_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues16Invoice.get_by_membership_no(1)
        self.assertEqual(res[0].id, 1)  # is a list

    def test_get_max_invoice_no(self):
        '''
        test get_max_invoice_no
        '''
        res = Dues16Invoice.get_max_invoice_no()
        self.assertEqual(res, 6)

    def test_existing_dues16_token(self):
        """
        test check_for_existing_dues16_token
        """
        res = Dues16Invoice.check_for_existing_dues16_token(
            u'ABCDEFGH')
        self.assertEqual(res, True)
        res2 = Dues16Invoice.check_for_existing_dues16_token(
            u'ABCDEFGHIK0000000000')
        self.assertEqual(res2, False)

    def test_get_monthly_stats(self):
        """
        Test get_monthly_stats.
        """
        stats = Dues16Invoice.get_monthly_stats()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'], D('-37.50'))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_reversal'], D('17.25'))
        self.assertAlmostEqual(stats[0]['amount_paid'], D('12.34'))
        self.assertEqual(stats[1]['month'], datetime(2015, 11, 1))
        self.assertAlmostEqual(stats[1]['amount_invoiced_normal'], D('87.47'))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_reversal'], D('101.64'))
        self.assertAlmostEqual(stats[1]['amount_paid'], D('10.53'))

    def test_decimality(self):
        """
        test the features of the 'amounts', esp. the format and persistence
        """

        # try to make another invoice with the same number
        def trigger_integrity_error_1():
            dues2 = Dues16Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues16-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_1)
        self.session.rollback()

        res = Dues16Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with the same string
        def trigger_integrity_error_2():
            dues2 = Dues16Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues16-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_2)
        self.session.rollback()

        res = Dues16Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with a non-decimal amount
        # InvalidOperation: Invalid literal for Decimal: '-37.50.20'
        def trigger_invalid_operation():
            dues2 = Dues16Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues16-0002',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50.20').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(InvalidOperation, trigger_invalid_operation)
        # trigger_invalid_operation()
        self.session.rollback()

        res = Dues16Invoice.get_all()
        self.assertEqual(len(res), 6)

        # now really store a new Dues16Invoice
        dues3 = Dues16Invoice(
            invoice_no=7,
            invoice_no_string=u'C3S-dues16-0002',
            invoice_date=date.today(),
            # invoice_amount=unicode(D('-37.50').to_eng_string()),
            invoice_amount=D('-37.50').to_eng_string(),
            member_id=1,
            membership_no=1,
            email=u'test@example.com',
            token=u'ABCDEFGH',
        )
        DBSession.add(dues3)
        DBSession.flush()

        res = Dues16Invoice.get_all()
        self.assertEqual(len(res), 7)
        self.assertEqual(dues3.id, 7)


class Dues17InvoiceModelTests(unittest.TestCase):
    """
    test the dues17 invoice model
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_staff.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)

            member2 = C3sMember(
                firstname=u'Franziska',
                lastname=u'Musterfrau',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO1',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member2)

            member3 = C3sMember(
                firstname=u'Jane',
                lastname=u'Somebody',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO2',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member3)

            dues1 = Dues17Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues17-0001',
                invoice_date=date(2015, 10, 01),
                invoice_amount=D('-37.50'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues1)

            dues2 = Dues17Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues17-0002-S',
                invoice_date=date(2015, 10, 02),
                invoice_amount=D('16.25'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'fa4wfjlasjfd',
            )
            dues2.is_reversal = True
            DBSession.add(dues2)

            dues3 = Dues17Invoice(
                invoice_no=3,
                invoice_no_string=u'C3S-dues17-0003',
                invoice_date=date(2015, 11, 25),
                invoice_amount=D('74.58'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'Jleifjsw9e',
            )
            DBSession.add(dues3)

            dues4 = Dues17Invoice(
                invoice_no=4,
                invoice_no_string=u'C3S-dues17-0004-S',
                invoice_date=date(2015, 11, 27),
                invoice_amount=D('23.85'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'f348h98sdf',
            )
            dues4.is_reversal = True
            DBSession.add(dues4)

            dues5 = Dues17Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues17-0005',
                invoice_date=date(2015, 11, 29),
                invoice_amount=D('12.89'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'sgdfoiddfg',
            )
            DBSession.add(dues5)

            dues6 = Dues17Invoice(
                invoice_no=6,
                invoice_no_string=u'C3S-dues17-0006-S',
                invoice_date=date(2015, 11, 30),
                invoice_amount=D('77.79'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'3o948n',
            )
            dues6.is_reversal = True
            DBSession.add(dues6)
            DBSession.flush()

            member1.set_dues17_payment(D('12.34'), date(2015, 10, 31))
            member2.set_dues17_payment(D('95.65'), date(2015, 11, 5))
            member3.set_dues17_payment(D('-85.12'), date(2015, 11, 30))

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_staff.db')

    def test_get_all(self):
        '''
        test get_all
        '''
        res = Dues17Invoice.get_all()
        self.assertEqual(len(res), 6)

    def test_get_by_invoice_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues17Invoice.get_by_invoice_no(1)
        self.assertEqual(res.id, 1)

    def test_get_by_membership_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues17Invoice.get_by_membership_no(1)
        self.assertEqual(res[0].id, 1)  # is a list

    def test_get_max_invoice_no(self):
        '''
        test get_max_invoice_no
        '''
        res = Dues17Invoice.get_max_invoice_no()
        self.assertEqual(res, 6)

    def test_existing_dues17_token(self):
        """
        test check_for_existing_dues17_token
        """
        res = Dues17Invoice.check_for_existing_dues17_token(
            u'ABCDEFGH')
        self.assertEqual(res, True)
        res2 = Dues17Invoice.check_for_existing_dues17_token(
            u'ABCDEFGHIK0000000000')
        self.assertEqual(res2, False)

    def test_get_monthly_stats(self):
        """
        Test get_monthly_stats.
        """
        stats = Dues17Invoice.get_monthly_stats()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'], D('-37.50'))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_reversal'], D('16.25'))
        self.assertAlmostEqual(stats[0]['amount_paid'], D('12.34'))
        self.assertEqual(stats[1]['month'], datetime(2015, 11, 1))
        self.assertAlmostEqual(stats[1]['amount_invoiced_normal'], D('87.47'))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_reversal'], D('101.64'))
        self.assertAlmostEqual(stats[1]['amount_paid'], D('10.53'))

    def test_decimality(self):
        """
        test the features of the 'amounts', esp. the format and persistence
        """

        # try to make another invoice with the same number
        def trigger_integrity_error_1():
            dues2 = Dues17Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues17-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_1)
        self.session.rollback()

        res = Dues17Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with the same string
        def trigger_integrity_error_2():
            dues2 = Dues17Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues17-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_2)
        self.session.rollback()

        res = Dues17Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with a non-decimal amount
        # InvalidOperation: Invalid literal for Decimal: '-37.50.20'
        def trigger_invalid_operation():
            dues2 = Dues17Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues17-0002',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50.20').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(InvalidOperation, trigger_invalid_operation)
        # trigger_invalid_operation()
        self.session.rollback()

        res = Dues17Invoice.get_all()
        self.assertEqual(len(res), 6)

        # now really store a new Dues17Invoice
        dues3 = Dues17Invoice(
            invoice_no=7,
            invoice_no_string=u'C3S-dues17-0002',
            invoice_date=date.today(),
            # invoice_amount=unicode(D('-37.50').to_eng_string()),
            invoice_amount=D('-37.50').to_eng_string(),
            member_id=1,
            membership_no=1,
            email=u'test@example.com',
            token=u'ABCDEFGH',
        )
        DBSession.add(dues3)
        DBSession.flush()

        res = Dues17Invoice.get_all()
        self.assertEqual(len(res), 7)
        self.assertEqual(dues3.id, 7)


class Dues18InvoiceModelTests(unittest.TestCase):
    """
    test the dues18 invoice model
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
        except:
            pass
        # engine = create_engine('sqlite:///test_model_staff.db')
        engine = create_engine('sqlite://')
        self.session = DBSession
        self.session.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)

            member2 = C3sMember(
                firstname=u'Franziska',
                lastname=u'Musterfrau',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO1',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member2)

            member3 = C3sMember(
                firstname=u'Jane',
                lastname=u'Somebody',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFO2',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=False,
                name_of_colsoc=u'',
                num_shares=u'23',
            )
            DBSession.add(member3)

            dues1 = Dues18Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues18-0001',
                invoice_date=date(2015, 10, 01),
                invoice_amount=D('-37.50'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues1)

            dues2 = Dues18Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues18-0002-S',
                invoice_date=date(2015, 10, 02),
                invoice_amount=D('16.25'),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'fa4wfjlasjfd',
            )
            dues2.is_reversal = True
            DBSession.add(dues2)

            dues3 = Dues18Invoice(
                invoice_no=3,
                invoice_no_string=u'C3S-dues18-0003',
                invoice_date=date(2015, 11, 25),
                invoice_amount=D('74.58'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'Jleifjsw9e',
            )
            DBSession.add(dues3)

            dues4 = Dues18Invoice(
                invoice_no=4,
                invoice_no_string=u'C3S-dues18-0004-S',
                invoice_date=date(2015, 11, 27),
                invoice_amount=D('23.85'),
                member_id=1,
                membership_no=2,
                email=u'test@example.com',
                token=u'f348h98sdf',
            )
            dues4.is_reversal = True
            DBSession.add(dues4)

            dues5 = Dues18Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues18-0005',
                invoice_date=date(2015, 11, 29),
                invoice_amount=D('12.89'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'sgdfoiddfg',
            )
            DBSession.add(dues5)

            dues6 = Dues18Invoice(
                invoice_no=6,
                invoice_no_string=u'C3S-dues18-0006-S',
                invoice_date=date(2015, 11, 30),
                invoice_amount=D('77.79'),
                member_id=1,
                membership_no=3,
                email=u'test@example.com',
                token=u'3o948n',
            )
            dues6.is_reversal = True
            DBSession.add(dues6)
            DBSession.flush()

            member1.set_dues18_payment(D('12.34'), date(2015, 10, 31))
            member2.set_dues18_payment(D('95.65'), date(2015, 11, 5))
            member3.set_dues18_payment(D('-85.12'), date(2015, 11, 30))

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_model_staff.db')

    def test_get_all(self):
        '''
        test get_all
        '''
        res = Dues18Invoice.get_all()
        self.assertEqual(len(res), 6)

    def test_get_by_invoice_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues18Invoice.get_by_invoice_no(1)
        self.assertEqual(res.id, 1)

    def test_get_by_membership_no(self):
        '''
        test get_by_invoice_no
        '''
        res = Dues18Invoice.get_by_membership_no(1)
        self.assertEqual(res[0].id, 1)  # is a list

    def test_get_max_invoice_no(self):
        '''
        test get_max_invoice_no
        '''
        res = Dues18Invoice.get_max_invoice_no()
        self.assertEqual(res, 6)

    def test_existing_dues18_token(self):
        """
        test check_for_existing_dues18_token
        """
        res = Dues18Invoice.check_for_existing_dues18_token(
            u'ABCDEFGH')
        self.assertEqual(res, True)
        res2 = Dues18Invoice.check_for_existing_dues18_token(
            u'ABCDEFGHIK0000000000')
        self.assertEqual(res2, False)

    def test_get_monthly_stats(self):
        """
        Test get_monthly_stats.
        """
        stats = Dues18Invoice.get_monthly_stats()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['month'], datetime(2015, 10, 1))
        self.assertAlmostEqual(stats[0]['amount_invoiced_normal'], D('-37.50'))
        self.assertAlmostEqual(
            stats[0]['amount_invoiced_reversal'], D('16.25'))
        self.assertAlmostEqual(stats[0]['amount_paid'], D('12.34'))
        self.assertEqual(stats[1]['month'], datetime(2015, 11, 1))
        self.assertAlmostEqual(stats[1]['amount_invoiced_normal'], D('87.47'))
        self.assertAlmostEqual(
            stats[1]['amount_invoiced_reversal'], D('101.64'))
        self.assertAlmostEqual(stats[1]['amount_paid'], D('10.53'))

    def test_decimality(self):
        """
        test the features of the 'amounts', esp. the format and persistence
        """

        # try to make another invoice with the same number
        def trigger_integrity_error_1():
            dues2 = Dues18Invoice(
                invoice_no=1,
                invoice_no_string=u'C3S-dues18-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_1)
        self.session.rollback()

        res = Dues18Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with the same string
        def trigger_integrity_error_2():
            dues2 = Dues18Invoice(
                invoice_no=2,
                invoice_no_string=u'C3S-dues18-0001',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(IntegrityError, trigger_integrity_error_2)
        self.session.rollback()

        res = Dues18Invoice.get_all()
        self.assertEqual(len(res), 6)

        # try to make another invoice with a non-decimal amount
        # InvalidOperation: Invalid literal for Decimal: '-37.50.20'
        def trigger_invalid_operation():
            dues2 = Dues18Invoice(
                invoice_no=5,
                invoice_no_string=u'C3S-dues18-0002',
                invoice_date=date.today(),
                invoice_amount=unicode(D('-37.50.20').to_eng_string()),
                member_id=1,
                membership_no=1,
                email=u'test@example.com',
                token=u'ABCDEFGH',
            )
            DBSession.add(dues2)
            DBSession.flush()

        self.assertRaises(InvalidOperation, trigger_invalid_operation)
        # trigger_invalid_operation()
        self.session.rollback()

        res = Dues18Invoice.get_all()
        self.assertEqual(len(res), 6)

        # now really store a new Dues18Invoice
        dues3 = Dues18Invoice(
            invoice_no=7,
            invoice_no_string=u'C3S-dues18-0002',
            invoice_date=date.today(),
            # invoice_amount=unicode(D('-37.50').to_eng_string()),
            invoice_amount=D('-37.50').to_eng_string(),
            member_id=1,
            membership_no=1,
            email=u'test@example.com',
            token=u'ABCDEFGH',
        )
        DBSession.add(dues3)
        DBSession.flush()

        res = Dues18Invoice.get_all()
        self.assertEqual(len(res), 7)
        self.assertEqual(dues3.id, 7)
