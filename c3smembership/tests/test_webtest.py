#!/bin/env/python
# -*- coding: utf-8 -*-
"""
This module holds tests for the webapp, webtest-style, see
http://webtest.readthedocs.org/en/latest/

There are two 'areas' covered:

- AccountantsFunctionalTests: for functionality accountants use
- FunctionalTests: for the basic parts of the webapp, i18n, ...
"""
# http://docs.pylonsproject.org/projects/pyramid/dev/narr/testing.html
#                                            #creating-functional-tests
# import os

from datetime import date

from pyramid import testing
from pyramid_mailer import get_mailer
from sqlalchemy import engine_from_config
import transaction
import unittest

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


class AccountantsFunctionalTests(unittest.TestCase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
            # print "closed and removed DBSession"
        except:
            pass
            # print "no session to close"
        # try:
        #    os.remove('test_webtest_accountants.db')
        #    #print "deleted old test database"
        # except:
        #    pass
        #    #print "never mind"
        # self.session = DBSession()
        my_settings = {
            # 'sqlalchemy.url': 'sqlite:///test_webtest_accountants.db',
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        self._insert_members()

        with transaction.manager:
                # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                # print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
            )
            staffer1.groups = [accountants_group]
            try:
                DBSession.add(accountants_group)
                DBSession.add(staffer1)
                DBSession.flush()
            except:
                print("it borked! (rut)")
                # pass

        from c3smembership import main
        app = main({}, **my_settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession.close()
        DBSession.remove()
        # os.remove('test_webtest_accountants.db')
        testing.tearDown()

    def _insert_members(self):
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
            member2 = C3sMember(  # german
                firstname=u'AAASomeFirstnäme',
                lastname=u'XXXSomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAR',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            member3 = C3sMember(  # german
                firstname=u'BBBSomeFirstnäme',
                lastname=u'AAASomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAZ',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            DBSession.add(member1)
            DBSession.add(member2)
            DBSession.add(member3)
            DBSession.flush()

    def get_dashboard_page(self, page_number, sort_property, sort_direction,
                           status):
        return self.testapp.get(
            '/dashboard?page-number={0}&sort-property={1}&sort-direction={2}'.format(
                page_number, sort_property, sort_direction), status=status,
        )

    def test_login_and_dashboard(self):
        """
        load the login form, dashboard, member detail
        """
        #
        # login
        #
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try invalid user
        form = res.form
        form['login'] = 'foo'
        form['password'] = 'bar'
        res2 = form.submit('submit')
        self.failUnless(
            'Please note: There were errors' in res2.body)
        # try valid user & invalid password
        form = res2.form
        form['login'] = 'rut'
        form['password'] = 'berry'
        res3 = form.submit('submit', status=200)
        # try valid user, valid password
        form = res2.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res3 = form.submit('submit', status=302)
        #
        # being logged in ...
        res4 = res3.follow()
        # print(res4.body)
        self.failUnless(
            'Acquisition of membership' in res4.body)
        # now that we are logged in,
        # the login view should redirect us to the dashboard
        res5 = self.testapp.get('/login', status=302)
        # so yes: that was a redirect
        res6 = res5.follow()
        # print(res4.body)
        self.failUnless(
            'Acquisition of membership' in res6.body)
        # choose number of applications shown
        res6a = self.testapp.get(
            '/dashboard',
            status=200,
            extra_environ={
                'num_display': '30',
            }
        )

        self.failUnless('Acquisition of membership' in res6a.body)
        res6a = self.get_dashboard_page(1, 'lastname', 'asc', 200)

        self.failUnless('Acquisition of membership' in res6a.body)
        # invalid sorting property
        # expect redirect to valid sorting property
        res6b = self.get_dashboard_page(1, 'invalid', 'asc', 400)

        # invalid sorting direction
        # expect displaying of the default sort direction
        res6b = self.get_dashboard_page(1, 'lastname', 'invalid', 200)

        # invalid page number: string
        # expect displaying of the first page
        res6b = self.get_dashboard_page('invalid', 'lastname', 'asc', 200)

        self.failUnless(
            'Number of data sets' in res6b.body)

        # change the number of items to show
        form = res6b.forms[0]
        form['page_size'] = "42"  # post a number: OK
        resX = form.submit('submit', status=200)

        form = resX.forms[0]
        form['page_size'] = "mooo"  # post a string: no good
        res7 = form.submit('submit', status=200)

        # member details
        #
        # now look at some members details with nonexistant id
        res7 = self.testapp.get('/detail/5000', status=302)
        res7a = res7.follow()
        self.failUnless('Membership tools' in res7a.body)

        # now look at some members details
        res7 = self.testapp.get('/detail/1', status=200)
        self.failUnless('Firstnäme' in res7.body)
        self.failUnless('Confirm signature' in res7.body)
        self.failUnless('Confirm payment' in res7.body)

        # if we are logged in and try to access the login page
        # we will be redirected to the dashboard straight away

        resL = self.testapp.get('/login', status=302)
        self.failUnless('302 Found' in resL.body)
        self.failUnless('http://localhost/dashboard' in resL.location)

        # finally log out ##################################################
        res9 = self.testapp.get('/logout', status=302)  # redirects to login
        res10 = res9.follow()
        self.failUnless('login' in res10.body)

    def test_switch_signature_and_payment(self):
        # login
        res = self.testapp.get('/login', status=200)
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # being logged in ...
        res3 = res2.follow()

        # have a set of headers with and without 'dashboard' in http referrer
        headers_dash = [
            ('Referer', 'http://this.app/dashboard')
        ]
        headers_nodash = [
            ('Referer', 'http://this.app/dashboard')
        ]

        # switch signature
        resD2a = self.testapp.get(
            '/switch_sig/1', status=302,
            headers=headers_dash)  # # # # # OFF
        resD2b = resD2a.follow()  # we are taken to the dashboard
        resD2b = self.testapp.get('/detail/1', status=200)
        # print resD2b.body
        self.assertTrue(
            "Eingang bestätigen" not in resD2b.body)
        resD2a = self.testapp.get(
            '/switch_sig/1', status=302,
            headers=headers_nodash
        )  # # # # # ON
        resD2b = resD2a.follow()  # we are taken to the dashboard
        resD2b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "Confirm signature" in resD2b.body)
        #
        # switch payment
        resD3a = self.testapp.get(
            '/switch_pay/1', status=302,
            headers=headers_dash
        )  # # # # OFF
        resD3b = resD3a.follow()  # we are taken to the dashboard
        resD3b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "Confirm payment" not in resD3b.body)
        resD3a = self.testapp.get('/switch_pay/1', status=302,
                                  headers=headers_dash)  # # # # ON
        resD3b = resD3a.follow()  # we are taken to the dashboard
        resD3b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "Confirm payment" in resD3b.body)
        #
        ####################################################################
        # delete an entry
        _num = C3sMember.get_number()
        resDel2 = self.testapp.get(
            '/delete/1?deletion_confirmed=1', status=302)
        _num2 = C3sMember.get_number()
        self.assertTrue(int(_num2) + 1 == int(_num))
        resDel3 = resDel2.follow()
        self.failUnless('was deleted' in resDel3.body)

        # finally log out ##################################################
        res9 = self.testapp.get('/logout', status=302)  # redirects to login
        res10 = res9.follow()
        self.failUnless('login' in res10.body)

    def test_dashboard_orderByFirstnameAsc_dashboardOrdered(self):
        res2 = self._login()
        res2 = self.get_dashboard_page(1, 'firstname', 'asc', 200)
        # print res2.body
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        # print "the first row: {}".format(first_member_row)
        first_name = first_member_row('td:nth-child(2)')
        # print "the first name: {}".format(first_name)
        self.assertEqual(u'AAASomeFirstnäme', first_name.text())

    def test_dashboard_orderByFirstnameDesc_dashboardOrdered(self):
        res2 = self._login()
        res2 = self.get_dashboard_page(1, 'firstname', 'desc', 200)
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        first_name = first_member_row('td:nth-child(2)')
        self.assertEqual(u'SomeFirstnäme', first_name.text())

    def test_dashboard_orderByLastnameAsc_dashboardOrdered(self):
        res2 = self._login()
        res2 = self.get_dashboard_page(1, 'lastname', 'asc', 200)
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(1)')
        self.assertEqual(u'AAASomeLastnäme', last_name.text())

    def test_dashboard_orderByLastnameDesc_dashboardOrdered(self):
        self._login()
        res2 = self.get_dashboard_page(1, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(1)')
        self.assertEqual(u'XXXSomeLastnäme', last_name.text())

    def test_dashboard_afterDelete_sameOrderAsBefore(self):
        self._login()
        self.get_dashboard_page(1, 'lastname', 'asc', 200)  # To set cookie with order & orderby
        # Delete member with lastname AAASomeLastnäme
        resdel = self.testapp.get('/delete/3?deletion_confirmed=1')
        resdel = resdel.follow()
        pq = self._get_pyquery(resdel.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(1)')
        self.assertEqual(u'SomeLastnäme', last_name.text())

    def test_dashboard_afterDelete_messageShown(self):
        self._login()
        resdel = self.testapp.get('/delete/1?deletion_confirmed=1')
        resdel = resdel.follow()
        pq = self._get_pyquery(resdel.body)
        message = pq('#message').text()
        self.assertTrue('was deleted' in message)

    def test_dashboard_onFirstPage_noPreviousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.get_dashboard_page(1, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res.body)
        self.assertEqual(len(pq("#navigate_previous")), 0)

    def test_dashboard_onFirstPage_nextLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.get_dashboard_page(1, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res.body)
        self.assertEqual(len(pq("#navigate_next")), 2)

    def test_dashboard_onSomePage_nextPreviousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.get_dashboard_page(2, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res.body)
        self.assertEqual(len(pq("#navigate_next")), 2)
        self.assertEqual(len(pq("#navigate_previous")), 2)

    def test_dashboard_onLastPage_previousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.get_dashboard_page(3, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res.body)
        self.assertEqual(len(pq("#navigate_previous")), 2)

    def test_dashboard_onLastPage_noNextLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.get_dashboard_page(3, 'lastname', 'desc', 200)
        pq = self._get_pyquery(res.body)
        self.assertEqual(len(pq("#navigate_next")), 0)

    def _get_pyquery(self, html):
        from pyquery import PyQuery as pq
        pure_html = ''.join(html.split('\n')[2:])
        pure_html = "<html>" + pure_html
        d = pq(pure_html)
        return d

    def _login(self):
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user, valid password
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        #
        # being logged in ...
        res3 = res2.follow()
        self.failUnless('Acquisition of membership' in res3.body)
        return res3

    def _change_num_to_show(self, num_to_show="1"):
        res = self.get_dashboard_page(1, 'lastname', 'desc', 200)
        form = res.forms[0]
        form['page_size'] = num_to_show
        resX = form.submit('submit', status=200)
        return resX

    def test_search_code(self):
        """
        load the search page and search for confirmation code
        """
        #
        # login
        #
        res3 = self._login()
        res3 = self.testapp.get('/search_codes', status=200)
        """
        we fill the confirmation code search form with a valid code,
        submit the form
        and check results
        """
        # try invalid code
        form = res3.forms[0]
        form['code_to_show'] = 'foo'
        res = form.submit()
        self.failUnless('Search for members' in res.body)
        self.failUnless('Code finden' in res.body)
        # now use existing code
        form = res.forms[0]
        # print form.fields
        form['code_to_show'] = 'ABCDEFGBAZ'
        # print form['code_to_show'].value
        res2 = form.submit()
        # print res2.body
        res = res2.follow()
        self.failUnless('Membership application details' in res.body)
        self.failUnless('ABCDEFGBAZ' in res.body)

    def test_search_people(self):
        """
        load the search page and search for people
        """
        #
        # login
        #
        res3 = self._login()
        res3 = self.testapp.get('/search_people', status=200)
        """
        we fill the confirmation code search form with a valid code,
        submit the form
        and check results
        """
        # try invalid code
        form = res3.forms[0]
        form['code_to_show'] = 'foo'
        res = form.submit()
        self.failUnless('Search for members' in res.body)
        self.failUnless('Personen finden' in res.body)
        # now use existing code
        form = res.forms[0]
        # print form.fields
        form['code_to_show'] = u'XXXSomeLastnäme'
        # print form['code_to_show'].value
        res = form.submit()
        # print res.body
        # res = res2.follow()
        # self.failUnless('Details for Member Application' in res.body)
        # self.failUnless('ABCDEFGBAZ' in res.body)
        # XXX FIXME

    def test_dashboard_regenerate_pdf(self):
        """
        load the dashboard and regenerate a PDF
        """
        #
        # login
        #
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user, valid password
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        #
        # being logged in ...
        res3 = res2.follow()
        self.failUnless('Acquisition of membership' in res3.body)

        """
        try to load a users PDF
        check size
        """
        # try invalid code
        pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
        self.failUnless('The resource was found at' in pdf.body)
        pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
        # now use existing code
        self.failUnless(80000 < len(pdf.body) < 220000)  # check pdf size

    # this test was commented out:
    # * it does not do what it claims to to... and fails anyway
    # * TODO: check if we have a test for this elsewhere... or repair it
    # def test_dashboard_mail_signature_confirmation(self):
    #     """
    #     load the dashboard and send out confirmation mails
    #     """
    #     #
    #     # login
    #     #
    #     res = self.testapp.get('/login', status=200)
    #     self.failUnless('login' in res.body)
    #     # try valid user, valid password
    #     form = res.form
    #     form['login'] = 'rut'
    #     form['password'] = 'berries'
    #     res2 = form.submit('submit', status=302)
    #     #
    #     # being logged in ...
    #     res3 = res2.follow()
    #     res3 = res3.follow()

    #     self.failUnless('Acquisition of membership' in res3.body)

    #     """
    #     try to send out the signature confirmation email
    #     """
    #     # try invalid code
    #     pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
    #     self.failUnless('The resource was found at' in pdf.body)
    #     pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
    #     # now use existing code
    #     self.failUnless(80000 < len(pdf.body) < 150000)  # check pdf size


class FunctionalTests(unittest.TestCase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
            # print("removed old DBSession ==============================")
        except:
            # print("no DBSession to remove =============================")
            pass
        # try:
        #    os.remove('test_webtest_functional.db')
        #    #print "deleted old test database"
        # except:
        #    pass
        #    #print "never mind"

        my_settings = {
            # 'sqlalchemy.url': 'sqlite:///test_webtest_functional.db',
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.notification_sender': 'c@example.com',
            'testing.mail_to_console': 'false'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        self.session = DBSession  # ()

        Base.metadata.create_all(engine)
        # dummy database entries for testing
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

        from c3smembership import main
        app = main({}, **my_settings)
        app.registry.get_mailer = get_mailer

        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        self.session.close()
        self.session.remove()
        # os.remove('test_webtest_functional.db')

    def test_base_template(self):
        """load the front page, check string exists"""
        res = self.testapp.get('/', status=200)
        self.failUnless('Cultural Commons Collecting Society' in res.body)
        self.failUnless(
            'Copyright 2014, C3S SCE' in res.body)

    # def test_faq_template(self):
    #     """load the FAQ page, check string exists"""
    #     res = self.testapp.get('/faq', status=200)
    #     self.failUnless('FAQ' in res.body)
    #     self.failUnless(
    #         'Copyright 2013, OpenMusicContest.org e.V.' in res.body)

    def test_lang_en_LOCALE(self):
        """load the front page, forced to english (default pyramid way),
        check english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/?_LOCALE_=en', status=200)
        self.failUnless(
            'Application for Membership of ' in res.body)

    def test_lang_en(self):
        """load the front page, set to english (w/ pretty query string),
        check english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/?en', status=302)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res1 = res.follow()
        self.failUnless(
            'Application for Membership of ' in res1.body)

# so let's test the app's obedience to the language requested by the browser
# i.e. will it respond to http header Accept-Language?

    # def test_accept_language_header_da(self):
    #     """check the http 'Accept-Language' header obedience: danish
    #     load the front page, check danish string exists"""
    #     res = self.testapp.reset()  # delete cookie
    #     res = self.testapp.get('/', status=200,
    #                            headers={
    #             'Accept-Language': 'da'})
    #     #print(res.body) #  if you want to see the pages source
    #     self.failUnless(
    #         '<input type="hidden" name="_LOCALE_" value="da"' in res.body)

    def test_accept_language_header_de_DE(self):
        """check the http 'Accept-Language' header obedience: german
        load the front page, check german string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get(
            '/', status=200,
            headers={
                'Accept-Language': 'de-DE'})
        # print(res.body) #  if you want to see the pages source
        self.failUnless(
            'Mitgliedschaftsantrag für die' in res.body)
        self.failUnless(
            '<input type="hidden" name="locale" value="de"' in res.body)

    def test_accept_language_header_en(self):
        """check the http 'Accept-Language' header obedience: english
        load the front page, check english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get(
            '/', status=200,
            headers={
                'Accept-Language': 'en'})
        # print(res.body) #  if you want to see the pages source
        self.failUnless(
            "I want to become"
            in res.body)

    # def test_accept_language_header_es(self):
    #     """check the http 'Accept-Language' header obedience: spanish
    #     load the front page, check spanish string exists"""
    #     res = self.testapp.reset()  # delete cookie
    #     res = self.testapp.get('/', status=200,
    #                            headers={
    #             'Accept-Language': 'es'})
    #     #print(res.body) #  if you want to see the pages source
    #     self.failUnless(
    #         'Luego de enviar el siguiente formulario,' in res.body)

    # def test_accept_language_header_fr(self):
    #     """check the http 'Accept-Language' header obedience: french
    #     load the front page, check french string exists"""
    #     res = self.testapp.reset()  # delete cookie
    #     res = self.testapp.get('/', status=200,
    #                            headers={
    #             'Accept-Language': 'fr'})
    #     #print(res.body) #  if you want to see the pages source
    #     self.failUnless(
    #         'En envoyant un courriel à data@example.com vous pouvez' in res.body)

    def test_no_cookies(self):
        """load the front page, check default english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get(
            '/', status=200,
            headers={
                'Accept-Language': 'af, cn'})  # ask for missing languages
        # print res.body
        self.failUnless('Application for Membership' in res.body)

#############################################################################
# check for validation stuff

    def test_form_lang_en_non_validating(self):
        """load the join form, check english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/?_LOCALE_=en', status=200)
        form = res.form
        # print(form.fields)
        # print(form.fields.values())
        form['firstname'] = 'John'
        # form['address2'] = 'some address part'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)

    def test_form_lang_de(self):
        """load the join form, check german string exists"""
        res = self.testapp.get('/?de', status=302)
        # print(res)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res2 = res.follow()
        # print(res2)
        # test for german translation of template text (lingua_xml)
        self.failUnless(
            'Mitgliedschaftsantrag für die' in res2.body)
        # test for german translation of form field label (lingua_python)
        self.failUnless('Vorname' in res2.body)

    def test_form_lang_LOCALE_de(self):
        """load the join form in german, check german string exists
        this time forcing german locale the pyramid way
        """
        res = self.testapp.get('/?_LOCALE_=de', status=200)
        # test for german translation of template text (lingua_xml)
        self.failUnless(
            'Mitgliedschaftsantrag für die' in res.body)
        # test for german translation of form field label (lingua_python)
        self.failUnless('Vorname' in res.body)

###########################################################################
# checking the success page that sends out email with verification link

    def test_check_email_en_wo_context(self):
        """try to access the 'check_email' page and be redirected
        check english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/check_email?en', status=302)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res1 = res.follow()
        # print(res1)
        self.failUnless(
            'Application for Membership of ' in str(
                res1.body),
            'expected string was not found in web UI')

###########################################################################
# checking the view that gets code and mail, asks for a password
    def test_verify_email_en_w_bad_code(self):
        """load the page in english,
        be redirected to the form (data is missing)
        check english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/verify/foo@shri.de/ABCD-----', status=200)
        self.failUnless(
            'Password' in res.body)
        form = res.form
        form['password'] = 'foobar'
        res2 = form.submit('submit')
        self.failUnless(
            'Password' in res2.body)

    def test_verify_email_en_w_good_code(self):
        """
        """
        res = self.testapp.reset()
        res = self.testapp.get('/verify/some@shri.de/ABCDEFGFOO', status=200)
        self.failUnless(
            'Password' in res.body)
        form = res.form
        form['password'] = 'arandompassword'
        res2 = form.submit('submit')
        # print res2.body
        self.failUnless(
            'C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf' in res2.body)
        # 'Your Email has been confirmed, Firstnäme Lastname!' in res.body)
        # res2 = self.testapp.get(
        #    '/C3S_SCE_AFM_Firstn_meLastname.pdf', status=200)
        # self.failUnless(len(res2.body) > 70000)

    def test_success_wo_data_en(self):
        """load the success page in english (via query_string),
        check for redirection and english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/success?en', status=302)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res1 = res.follow()
        # print(res1)
        self.failUnless(  # check text on page redirected to
            'Please fill out the form' in str(
                res1.body),
            'expected string was not found in web UI')

    def test_success_pdf_wo_data_en(self):
        """
        try to load a pdf (which must fail because the form was not used)
        check for redirection to the form and test string exists
        """
        res = self.testapp.reset()
        res = self.testapp.get(
            '/C3S_SCE_AFM_ThefirstnameThelastname.pdf',
            status=302)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res1 = res.follow()
        # print(res1)
        self.failUnless(  # check text on page redirected to
            'Please fill out the form' in str(
                res1.body),
            'expected string was not found in web UI')

    def test_email_confirmation(self):
        """
        test email confirmation form and PDF download
        with a known login/dataset
        """
        res = self.testapp.reset()
        res = self.testapp.get('/verify/some@shri.de/ABCDEFGFOO', status=200)
        # print(res.body)
        form = res.form
        form['password'] = 'arandompassword'
        res2 = form.submit('submit')
        # print res2.body
        self.failUnless("Load your PDF" in res2.body)
        self.failUnless(
            "/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf" in res2.body)
        # load the PDF, check size
        res3 = self.testapp.get(
            '/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf',
            status=200
        )
        # print("length of result: %s") % len(res3.body)
        # print("body result: %s") % (res3.body)  # ouch, PDF content!
        self.failUnless(80000 < len(res3.body) < 220000)  # check pdf size

    def test_email_confirmation_wrong_mail(self):
        """
        test email confirmation with a wrong email
        """
        res = self.testapp.reset()
        res = self.testapp.get(
            '/verify/NOTEXISTS@shri.de/ABCDEFGHIJ', status=200)
        # print(res.body)
        self.failUnless("Please enter your password." in res.body)
        # XXX this test shows nothing interesting

    def test_email_confirmation_wrong_code(self):
        """
        test email confirmation with a wrong code
        """
        res = self.testapp.reset()
        res = self.testapp.get('/verify/foo@shri.de/WRONGCODE', status=200)
        # print(res.body)
        self.failUnless("Please enter your password." in res.body)

    def test_success_check_email(self):
        """
        test "check email" success page with wrong data:
        this should redirect to the form.
        """
        res = self.testapp.reset()
        res = self.testapp.get('/check_email', status=302)

        res2 = res.follow()
        self.failUnless("Please fill out the form" in res2.body)
