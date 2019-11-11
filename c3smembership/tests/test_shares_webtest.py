# -*- coding: utf-8 -*-
"""
Test shares by using WebTest
"""

from datetime import (datetime, date)
import unittest

import transaction
from webtest import TestApp

from pyramid import testing
from sqlalchemy import engine_from_config

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.shares import Shares
from c3smembership.data.model.base.staff import Staff


DEBUG = False


class SharesTests(unittest.TestCase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        db_session = DBSession()

        with transaction.manager:
            # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            db_session.add(accountants_group)
            db_session.flush()
            # staff personnel
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
            )
            staffer1.groups = [accountants_group]
            db_session.add(accountants_group)
            db_session.add(staffer1)
            db_session.flush()

        app = main({}, **my_settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        """
        Tear down the test case
        """
        DBSession().close()
        DBSession.remove()
        testing.tearDown()

    @classmethod
    def make_member_with_shares(cls):
        """
        Create member and shares database records
        """
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
            shares1 = Shares(
                number=2,
                date_of_acquisition=date.today(),
                reference_code=u'ABCDEFGH',
                signature_received=True,
                signature_received_date=date(2014, 6, 7),
                payment_received=True,
                payment_received_date=date(2014, 6, 8),
                signature_confirmed=True,
                signature_confirmed_date=date(2014, 6, 8),
                payment_confirmed=True,
                payment_confirmed_date=date(2014, 6, 9),
                accountant_comment=u'no comment',
            )
            member1.shares = [shares1]
            shares2 = Shares(
                number=23,
                date_of_acquisition=date.today(),
                reference_code=u'IJKLMNO',
                signature_received=True,
                signature_received_date=date(2014, 1, 7),
                payment_received=True,
                payment_received_date=date(2014, 1, 8),
                signature_confirmed=True,
                signature_confirmed_date=date(2014, 1, 8),
                payment_confirmed=True,
                payment_confirmed_date=date(2014, 1, 9),
                accountant_comment=u'not connected',
            )
        db_session = DBSession()
        db_session.add(member1)
        db_session.add(shares1)
        db_session.add(shares2)

    @classmethod
    def make_member_with_shares2(cls):
        """
        Create member and shares database records
        """
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
            shares1 = Shares(
                number=2,
                date_of_acquisition=date.today(),
                reference_code=u'ABCDEFGH',
                signature_received=True,
                signature_received_date=date(2014, 6, 7),
                payment_received=True,
                payment_received_date=date(2014, 6, 8),
                signature_confirmed=True,
                signature_confirmed_date=date(2014, 6, 8),
                payment_confirmed=True,
                payment_confirmed_date=date(2014, 6, 9),
                accountant_comment=u'no comment',
            )
            member1.shares = [shares1]
        db_session = DBSession()
        db_session.add(member1)
        db_session.add(shares1)

    @classmethod
    def make_unconnected_shares(cls):
        """
        Create shares package without member
        """
        with transaction.manager:
            shares2 = Shares(
                number=23,
                date_of_acquisition=date.today(),
                reference_code=u'IJKLMNO',
                signature_received=True,
                signature_received_date=date(2014, 1, 7),
                payment_received=True,
                payment_received_date=date(2014, 1, 8),
                signature_confirmed=True,
                signature_confirmed_date=date(2014, 1, 8),
                payment_confirmed=True,
                payment_confirmed_date=date(2014, 1, 9),
                accountant_comment=u'not connected',
            )
        DBSession().add(shares2)

    def test_shares_detail(self):
        '''
        tests for the shares_detail view
        '''
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/shares_edit/1', status=403)
        self.assertTrue('Access was denied to this resource' in res.body)
        res = self.testapp.get('/login', status=200)
        self.assertTrue('login' in res.body)
        # try valid user
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # being logged in ...
        res3 = res2.follow()  # being redirected to dashboard with parameters
        self.assertTrue('Acquisition of membership' in res3.body)
        # now look at a shares package
        res = self.testapp.get('/shares_detail/1', status=302)
        res2 = res.follow()
        # we were redirected to the menberships list
        # because the shares package did not exist
        self.assertTrue(
            'This shares id was not found in the database!' in res2.body)
        self.assertTrue('Membership tools' in res2.body)

        self.make_member_with_shares()

        # now look at a shares package
        res = self.testapp.get('/shares_detail/1', status=200)
        self.assertTrue('<h1>Details for Shares #1</h1>' in res.body)
        self.assertTrue('SomeFirstnäme SomeLastnäme' in res.body)
        self.assertTrue('ABCDEFGH' in res.body)

    def test_shares_edit(self):
        '''
        tests for the shares_edit view
        '''
        # unauthorized access must be prevented
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/shares_edit/1', status=403)
        self.assertTrue('Access was denied to this resource' in res.body)
        res = self.testapp.get('/login', status=200)
        self.assertTrue('login' in res.body)
        # try valid user
        form = res.form
        form['login'] = u'rut'
        form['password'] = u'berries'
        res2 = form.submit('submit', status=302)
        # # being logged in ...
        res3 = res2.follow()  # being redirected to dashboard with parameters
        self.assertTrue('Acquisition of membership' in res3.body)

        # no member in DB, so redirecting to dashboard
        res = self.testapp.get('/shares_edit/1', status=302)
        res2 = res.follow()

        self.make_member_with_shares()

        # now there is a member with shares in the DB
        #
        # lets try invalid input
        res = self.testapp.get('/shares_edit/foo', status=302)
        res2 = res.follow()
        self.assertTrue('Members' in res2.body)

        # now try valid id
        res = self.testapp.get('/shares_edit/1', status=200)
        self.assertTrue('Edit Details for Shares' in res.body)

        # now we change details, really editing that member
        form = res.form

        self.assertTrue('2' in form['number'].value)
        field_id_dict = self.__get_field_id_dict(form)
        self.assertTrue(datetime.today().strftime(
            '%Y-%m-%d') in field_id_dict['date_of_acquisition'].value)
        form['number'] = u'3'
        field_id_dict['date_of_acquisition'].value = u'2015-01-02'

        # try to submit now. this must fail,
        # because the date of birth is wrong
        # ... and other dates are missing
        res2 = form.submit('submit', status=200)

        # check data in DB
        member = C3sMember.get_by_id(1)
        self.assertEqual(member.shares[0].number, 3)
        self.assertTrue(str(
            member.shares[0].date_of_acquisition) in str(datetime(2015, 1, 2)))

    def test_shares_delete(self):
        '''
        tests for the shares_delete view
        '''
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/shares_edit/1', status=403)
        self.assertTrue('Access was denied to this resource' in res.body)
        res = self.testapp.get('/login', status=200)
        self.assertTrue('login' in res.body)
        # try valid user
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # # being logged in ...
        res3 = res2.follow()  # being redirected to dashboard with parameters
        self.assertTrue(
            'Acquisition of membership' in res3.body)

        self.make_member_with_shares()

        # now look at a shares package
        res = self.testapp.get('/shares_detail/1', status=200)
        self.assertTrue('<h1>Details for Shares #1</h1>' in res.body)
        self.assertTrue('SomeFirstnäme SomeLastnäme' in res.body)
        self.assertTrue('ABCDEFGH' in res.body)

        # try to delete a non-existing package
        res = self.testapp.get('/shares_delete/123', status=302)
        res2 = res.follow()
        self.assertTrue(
            'This shares package 123 was not found in the DB.' in res2.body)

        # try to delete an existing package
        res = self.testapp.get('/shares_delete/1', status=302)
        res2 = res.follow()
        self.assertTrue(
            'This shares package 1 still has a member owning it.' in res2.body)
        res = self.testapp.get('/delete/1', status=302)
        res2 = res.follow()

        res = self.testapp.get('/shares_detail/1', status=200)
        self.assertTrue('<h1>Details for Shares #1</h1>' in res.body)
        self.assertTrue('ABCDEFGH' in res.body)

    @classmethod
    def __get_field_id_dict(cls, form):
        """
        Get a field id dict from the form

        Fields are not easily accessible from the form by id. Therefore, create
        a dictionary which maps the id to its field. Using the dict increases
        performance in case many fields have to be found by id.

        Args:
            form: webtest.forms.Form. The form to be transformed into a field
                id dict.

        Returns:
            dict mapping the id to its field.
        """
        field_id_dict = {}
        for key in form.fields.keys():
            fields = form.fields[key]
            for field in fields:
                field_id_dict[field.id] = field
        return field_id_dict
