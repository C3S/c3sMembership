# -*- coding: utf-8  -*-
import os
import unittest
import transaction
#from pyramid.config import Configurator
from pyramid import testing
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from c3smembership.models import (
    DBSession,
    Base,
    C3sMember
)
DEBUG = False


class C3sMembershipModelTestBase(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.remove()
            #print("removing old DBSession ===================================")
        except:
            #print("no DBSession to remove ===================================")
            pass
        engine = create_engine('sqlite:///test_models.db')
        self.session = DBSession
        DBSession.configure(bind=engine)  # XXX does influence self.session!?!
        Base.metadata.create_all(engine)


    def tearDown(self):
        self.session.close()
        self.session.remove()
        os.remove('test_models.db')

    def _getTargetClass(self):
        from c3smembership.models import C3sMember
        return C3sMember

    def _makeOne(self,
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
                 num_shares=u'23',
                 ):
        #print "type(self.session): " + str(type(self.session))
        return self._getTargetClass()(  # order of params DOES matter
            firstname, lastname, email,
            password,
            address1, address2, postcode,
            city, country, locale,
            date_of_birth, email_is_confirmed, email_confirm_code,
            num_shares,
            #is_composer, is_lyricist, is_producer, is_remixer, is_dj,
            date_of_submission,
            #invest_member,
            membership_type,
            member_of_colsoc, name_of_colsoc,
            #opt_band, opt_URL
            )

    def _makeAnotherOne(self,
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
                        num_shares=u'23',
                        ):
        return self._getTargetClass()(  # order of params DOES matter
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
        instance = self._makeOne()
        #print(instance.address1)
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

    def test_get_by_code(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        myMembershipSigneeClass = self._getTargetClass()
        instance_from_DB = myMembershipSigneeClass.get_by_code(u'ABCDEFGHIK')
        #self.session.commit()
        #self.session.remove()
        #print instance_from_DB.email
        if DEBUG:
            print "myMembershipSigneeClass: " + str(myMembershipSigneeClass)
            #        print "str(myUserClass.get_by_username('SomeUsername')): "
            # + str(myUserClass.get_by_username('SomeUsername'))
            #        foo = myUserClass.get_by_username(instance.username)
            #        print "test_get_by_username: type(foo): " + str(type(foo))
        self.assertEqual(instance.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_DB.email, u'some@shri.de')

    def test_get_by_id(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        self.session.flush()
        _id = instance.id
        _date_of_birth = instance.date_of_birth
        _date_of_submission = instance.date_of_submission
        myMembershipSigneeClass = self._getTargetClass()
        instance_from_DB = myMembershipSigneeClass.get_by_id(_id)
        #self.session.commit()
        #self.session.remove()
        #print instance_from_DB.email
        if DEBUG:
            print "myMembershipSigneeClass: " + str(myMembershipSigneeClass)
            #        print "str(myUserClass.get_by_username('SomeUsername')): "
            # + str(myUserClass.get_by_username('SomeUsername'))
            #        foo = myUserClass.get_by_username(instance.username)
            #        print "test_get_by_username: type(foo): " + str(type(foo))
        self.assertEqual(instance_from_DB.firstname, u'SomeFirstnäme')
        self.assertEqual(instance_from_DB.lastname, u'SomeLastnäme')
        self.assertEqual(instance_from_DB.email, u'some@shri.de')
        self.assertEqual(instance_from_DB.address1, u'addr one')
        self.assertEqual(instance_from_DB.address2, u'addr two')
        self.assertEqual(instance_from_DB.postcode, u'12345')
        self.assertEqual(instance_from_DB.city, u'Footown Mäh')
        self.assertEqual(instance_from_DB.country, u'Foocountry')
        self.assertEqual(instance_from_DB.locale, u'DE')
        self.assertEqual(instance_from_DB.date_of_birth, _date_of_birth)
        self.assertEqual(instance_from_DB.email_is_confirmed, False)
        self.assertEqual(instance_from_DB.email_confirm_code, u'ABCDEFGHIK')
        self.assertEqual(instance_from_DB.date_of_submission, _date_of_submission)
        self.assertEqual(instance_from_DB.membership_type, u'normal')
        self.assertEqual(instance_from_DB.member_of_colsoc, True)
        self.assertEqual(instance_from_DB.name_of_colsoc, u'GEMA')
        self.assertEqual(instance_from_DB.num_shares, u'23')

    def test_delete_by_id(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        myMembershipSigneeClass = self._getTargetClass()
        instance_from_DB = myMembershipSigneeClass.get_by_id('1')
        del_instance_from_DB = myMembershipSigneeClass.delete_by_id('1')
        #print del_instance_from_DB
        instance_from_DB = myMembershipSigneeClass.get_by_id('1')
        self.assertEqual(None, instance_from_DB)

    def test_check_user_or_None(self):
        instance = self._makeOne()
        #session = DBSession()
        self.session.add(instance)
        myMembershipSigneeClass = self._getTargetClass()
        # get first dataset (id = 1)
        result1 = myMembershipSigneeClass.check_user_or_None('1')
        #print check_user_or_None
        self.assertEqual(1, result1.id)
        # get invalid dataset
        result2 = myMembershipSigneeClass.check_user_or_None('1234567')
        #print check_user_or_None
        self.assertEqual(None, result2)

    def test_check_for_existing_confirm_code(self):
        instance = self._makeOne()
        self.session.add(instance)
        myMembershipSigneeClass = self._getTargetClass()

        result1 = myMembershipSigneeClass.check_for_existing_confirm_code(
            u'ABCDEFGHIK')
        print result1  # True
        self.assertEqual(result1, True)
        result2 = myMembershipSigneeClass.check_for_existing_confirm_code(
            u'ABCDEFGHIK0000000000')
        #print result2  # False
        self.assertEqual(result2, False)

    def test_member_listing(self):
        instance = self._makeOne()
        self.session.add(instance)
        instance2 = self._makeAnotherOne()
        self.session.add(instance2)
        myMembershipSigneeClass = self._getTargetClass()

        result1 = myMembershipSigneeClass.member_listing("id")
        self.failUnless(result1[0].firstname == u"SomeFirstnäme")
        self.failUnless(result1[1].firstname == u"SomeFirstnäme")
        self.failUnless(result1[2].firstname == u"SomeFirstname")


class TestMemberListing(C3sMembershipModelTestBase):
    def setUp(self):
        super(TestMemberListing, self).setUp()
        instance = self._makeOne(lastname=u"ABC", firstname=u'xyz', email_confirm_code=u'0987654321')
        self.session.add(instance)
        instance = self._makeAnotherOne(lastname=u"DEF", firstname=u'abc', email_confirm_code=u'19876543210')
        self.session.add(instance)
        instance = self._makeAnotherOne(lastname=u"GHI", firstname=u'def', email_confirm_code=u'098765432101')
        self.session.add(instance)
        self.session.flush()
        self.class_under_test = self._getTargetClass()

    def test_orderByLastname_sortedByLastname(self):
        print "now test " * 45
        result = self.class_under_test.member_listing(order_by='lastname')
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].lastname)
        self.assertEqual("GHI", result[-1].lastname)

    def test_orderByLastnameOrderAsc_sortedByLastname(self):
        result = self.class_under_test.member_listing(order_by='lastname', order="asc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("ABC", result[0].lastname)
        self.assertEqual("GHI", result[-1].lastname)

    def test_orderByLastnameOrderDesc_sortedByLastname(self):
        result = self.class_under_test.member_listing(order_by='lastname', order="desc")
        self.assertIsNotNone(result)
        self.assertIsNotNone(result[0])
        self.assertEqual("GHI", result[0].lastname)
        self.assertEqual("ABC", result[-1].lastname)

    def test_orderByInvalidName_raisesException(self):
        self.assertRaises(self.class_under_test.member_listing, order_by='unknown', order="desc")
        self.assertRaises(self.class_under_test.member_listing, order_by=None, order="desc")
        self.assertRaises(self.class_under_test.member_listing, order_by="", order="desc")

    def test_orderInvalid_raisesException(self):
        self.assertRaises(self.class_under_test.member_listing, order_by='lastname', order="unknown")
        self.assertRaises(self.class_under_test.member_listing, order_by='lastname', order="")
        self.assertRaises(self.class_under_test.member_listing, order_by='lastname', order=None)
