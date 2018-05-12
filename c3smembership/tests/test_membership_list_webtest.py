#!/bin/env/python
# -*- coding: utf-8 -*-
"""
Tests for c3smembership.membership_list
"""
from datetime import (
    date,
    datetime,
    timedelta,
)
from pyramid import testing
from sqlalchemy import engine_from_config
import transaction
import unittest
# import webtest
from webtest import TestApp

from c3smembership import main
from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.models import (
    C3sMember,
    C3sStaff,
    Group,
    Shares,
)

DEBUG = False


class MemberTestsBase(unittest.TestCase):
    def setUp(self):
        """
        Setup test cases
        """
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        DBSession.close()
        DBSession.remove()
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        # self._insert_members()

        with transaction.manager:
            # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            DBSession.add(accountants_group)
            DBSession.flush()
            # staff personnel
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            DBSession.add(accountants_group)
            DBSession.add(staffer1)
            DBSession.flush()

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
                locale=u"de",
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
            shares1_m1 = Shares(
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
            member1.shares = [shares1_m1]
            shares2_m1 = Shares(
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
            member1.shares.append(shares2_m1)
            member1.membership_accepted = True

            member2 = C3sMember(  # english
                firstname=u'AAASomeFirstnäme',
                lastname=u'XXXSomeLastnäme',
                email=u'some2@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"en",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAR',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'2',
            )
            founding_member3 = C3sMember(  # english
                firstname=u'BBBSomeFirstnäme',
                lastname=u'YYYSomeLastnäme',
                email=u'some3@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"en",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCBARdungHH_',
                password=u'anotherrandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'2',
            )
            member4_lost = C3sMember(
                firstname=u'Resigned',
                lastname=u'Smith',
                email=u'resigned.smith@example.com',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"en",
                date_of_birth=date(1980, 1, 2),
                email_is_confirmed=False,
                email_confirm_code=u'RESIGNEDSMITH',
                password=u'arandompassword',
                date_of_submission=date.today() - timedelta(days=370),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'2',
            )

            DBSession.add(shares1_m1)
            DBSession.add(shares2_m1)
            DBSession.add(member1)
            DBSession.add(member2)
            DBSession.add(founding_member3)
            DBSession.add(member4_lost)

        app = main({}, **my_settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        """
        Tear down all test cases
        """
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    def __login(self):
        """
        Log into the membership backend
        """
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body.decode('utf-8'))
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res = form.submit('submit', status=302)
        # being logged in ...
        self.__validate_dashboard_redirect(res)

    def __validate_dashboard_redirect(self, res):
        """
        Validate that res is redirecting to the dashboard
        """
        res = res.follow()  # being redirected to dashboard with parameters
        self.__validate_dashboard(res)

    def __validate_dashboard(self, res):
        """
        Validate that res is the dashboard
        """
        self.failUnless('Dashboard' in res.body.decode('utf-8'))


class MakeMergeMemberTests(MemberTestsBase):

    def test_make_member_view(self):
        '''
        Tests for the make member view
        '''
        res = self.testapp.reset()  # delete cookies

        m1 = C3sMember.get_by_id(1)
        afm_id = m1.id

        res = self.testapp.get(
            '/make_member/{afm_id}'.format(afm_id=afm_id), status=403)
        self.failUnless('Access was denied to this resource' \
            in res.body.decode('utf-8'))

        self._MemberTestsBase__login()

        # try bad id
        res = self.testapp.get(
            '/make_member/12345', status=302)  # redirect to dashboard!

        # try correct id, but membership already accepted
        self.assertTrue(m1.membership_accepted is True)
        res = self.testapp.get(
            '/make_member/{afm_id}'.format(
                afm_id=afm_id), status=302)  # redirect!
        res2 = res.follow()

        # reset membership acceptance to False, try again
        m1.membership_accepted = False
        self.assertTrue(m1.membership_accepted is False)
        res = self.testapp.get(
            '/make_member/{afm_id}'.format(
                afm_id=afm_id), status=302)  # redirect!

        res2 = res.follow()

        # set reception of signature & payment, try again
        m1.signature_received = True
        m1.payment_received = True
        self.assertTrue(m1.membership_accepted is False)
        self.assertTrue(m1.signature_received is True)
        self.assertTrue(m1.payment_received is True)

        # we need to send a Referer-header, so the redirect works
        _headers = {'Referer': 'http://this.web/detail/1'}
        # wo_req = wor()
        res = self.testapp.get(
            '/make_member/{afm_id}'.format(
                afm_id=afm_id),
            headers=_headers,
            status=200)  # 200 -- OK

        # some assertions
        self.assertTrue('You are about to make this person a proper member '
                        'of C3S SCE:' in res.body.decode('utf-8'))
        self.assertTrue('Membership Number to be given: 1' \
            in res.body.decode('utf-8'))
        self.assertTrue('form action="http://localhost/make_member/1' \
            in res.body.decode('utf-8'))
        self.assertTrue(
            u'SomeFirstnäme SomeLastnäme' in res.body.decode('utf-8'))

        # this member must not be accepted yet
        self.assertTrue(m1.membership_accepted is False)
        # this member must not have a membership number yet
        self.assertTrue(m1.membership_number is None)
        # this members membership date is not set to a recent date
        self.assertEqual(m1.membership_date, date(1970, 01, 01))
        # this member holds no shares yet
        m1.shares = []
        self.assertTrue(len(m1.shares) is 0)
        # now, use that form to supply a "membership_accepted_date"
        form = res.form
        form['membership_date'] = date.today().strftime('%Y-%m-%d')
        res2 = form.submit()

        # check whether m1 is now an accepted member
        self.assertTrue(m1.membership_accepted is True)
        self.assertTrue(m1.membership_number is 1)
        self.assertTrue(m1.membership_date is not None)
        self.assertEqual(len(m1.shares), 1)
        # we are redirected to members details page
        res3 = res2.follow()
        # this now is a member!
        self.failUnless('Details for Member Application #1' in res3.body)
        self.failUnless("""<td>membership_accepted</td>
            <td>
                Yes
            </td>""" in res3.body)

    def test_merge_member_view(self):
        '''
        Tests for the merge_member_view
        '''
        res = self.testapp.reset()  # delete cookies

        afm = C3sMember.get_by_id(2)  # an application
        m = C3sMember.get_by_id(1)  # an accepted member

        self.assertTrue(afm.membership_accepted is False)
        self.assertEqual(afm.num_shares, 2)
        self.assertEqual(afm.shares, [])

        self.assertTrue(m.membership_accepted is True)
        self.assertEqual(m.num_shares, 23)
        self.assertEqual(len(m.shares), 2)  # 2 shares packages

        # try unauthenticated access -- must fail!
        res = self.testapp.get(
            '/merge_member/{afm_id}/{mid}'.format(
                afm_id=afm.id,
                mid=m.id),
            status=403)
        self.failUnless('Access was denied to this resource' \
            in res.body.decode('utf-8'))

        # authenticate/authorize
        self._MemberTestsBase__login()

        res = self.testapp.get(
            '/merge_member/{afm_id}/{mid}'.format(
                afm_id=afm.id,
                mid=m.id),
            status=302)  # redirect!

        self.assertTrue(afm.membership_accepted is False)
        self.assertTrue(m.membership_accepted is True)
        self.assertEqual(m.num_shares, 25)
        self.assertEqual(len(m.shares), 3)  # 2 shares packages


class MembershipListTests(MemberTestsBase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    """

    def test_member_list_date_pdf_view(self):  # code lines 80-283
        '''
        Tests for the member_list_aufstockers_view

        If called with a faulty date in URL (not parseable) expect redirection
        to error page.

        Else: expect a PDF.
        '''
        _date = '2016-02-11'  # any date
        _bad_date = '2016-02-111111'  # any bad date
        res = self.testapp.reset()  # delete cookies
        res = self.testapp.get('/aml-' + _date + '.pdf', status=403)
        self.failUnless('Access was denied to this resource' \
            in res.body.decode('utf-8'))

        self._MemberTestsBase__login()

        # try a bad date (== not convertable to a date)
        res = self.testapp.get('/aml-' + _bad_date + '.pdf', status=302)
        self.assertTrue('error' in res)
        res2 = res.follow()  # follow redirect
        self.assertTrue("Invalid date!" in res2.body)
        self.assertTrue("'2016-02-111111' does not compute!" in res2.body)
        self.assertTrue('try again, please! (YYYY-MM-DD)' in res2.body)

        # try with valid date in URL
        res = self.testapp.get('/aml-' + _date + '.pdf', status=200)
        # print(res)
        self.assertTrue(20000 < len(res.body) < 100000)
        self.assertEqual(res.content_type, 'application/pdf')

        # missing coverage of code lines  # 125-134, 192-225,
        m1 = C3sMember.get_by_id(1)
        m1.membership_date = date(2015, 01, 01)
        m1.membership_number = 42
        m1.shares[0].date_of_acquisition = date(2015, 01, 01)
        m1.shares[1].date_of_acquisition = date(2015, 01, 02)

        # try with valid date in URL
        res = self.testapp.get('/aml-' + _date + '.pdf', status=200)
        # print(res)
        self.assertTrue(20000 < len(res.body) < 100000)
        self.assertEqual(res.content_type, 'application/pdf')
        # XXX TODO: missing coverage of membership_loss cases...

    def test_member_list_alphabetical_view(self):  # code lines 286-325
        '''
        tests for the member_list_alphabetical_view
        '''
        res = self.testapp.reset()  # delete cookies
        res = self.testapp.get('/aml', status=403)
        self.failUnless('Access was denied to this resource' \
            in res.body.decode('utf-8'))

        self._MemberTestsBase__login()

        member4_lost = C3sMember.get_by_id(4)
        member4_lost.membership_accepted = True
        member4_lost.membership_number = 9876

        res = self.testapp.get('/aml', status=200)
        self.assertTrue('2 Mitglieder' in res.body.decode('utf-8'))

        member4_lost.membership_date = date.today() - timedelta(days=365)
        member4_lost.membership_loss_date = \
            date.today() - timedelta(days=30)

        res = self.testapp.get('/aml', status=200)
        self.assertTrue('1 Mitglieder' in res.body.decode('utf-8'))

    def test_membership_listing_backend_view(self):  # code lines 328-411
        '''
        tests for the member listing view for the backend (html with links)
        '''
        res = self.testapp.reset()  # delete cookies
        res = self.testapp.get('/memberships', status=403)
        #
        #  must find out how the machdict could be set right,
        #  so it is not None --> keyerror
        #
        #
        self.failUnless('Access was denied to this resource' \
            in res.body.decode('utf-8'))

        self._MemberTestsBase__login()

        res = self.testapp.get('/memberships', status=200)

        self.assertTrue('Page 1 of 1' in res.body.decode('utf-8'))
        self.assertTrue(u'SomeFirstnäme' in res.body.decode('utf-8'))
