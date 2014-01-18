#!/bin/env/python
# -*- coding: utf-8 -*-
# http://docs.pylonsproject.org/projects/pyramid/dev/narr/testing.html
#                                            #creating-functional-tests
import os
import unittest
from pyramid import testing
from c3smembership.models import (
    DBSession,
    Base,
    C3sMember,
    C3sStaff,
    Group,
)
from sqlalchemy import engine_from_config
import transaction
from datetime import date


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
            #print "closed and removed DBSession"
        except:
            pass
            #print "no session to close"
        try:
            os.remove('test_webtest_accountants.db')
            #print "deleted old test database"
        except:
            pass
            #print "never mind"
       # self.session = DBSession()
        my_settings = {
            'sqlalchemy.url': 'sqlite:///test_webtest_accountants.db',
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
                print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
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
        os.remove('test_webtest_accountants.db')
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
        res4 = res4.follow()
        #print(res4.body)
        self.failUnless(
            'Dashboard' in res4.body)
        # now that we are logged in,
        # the login view should redirect us to the dashboard
        res5 = self.testapp.get('/login', status=302)
        # so yes: that was a redirect
        res6 = res5.follow()
        res6 = res6.follow()
        #print(res4.body)
        self.failUnless(
            'Dashboard' in res6.body)
        # choose number of applications shown
        res6a = self.testapp.get(
            '/dashboard',
            status=302,
            extra_environ={
                'num_display': '30',
            }
        )
        res6a = res6a.follow()

        self.failUnless('<h1>Dashboard</h1>' in res6a.body)
        res6a = self.testapp.get(
            '/dashboard/1/id/asc', status=200,
        )

        self.failUnless('<h1>Dashboard</h1>' in res6a.body)
        # try an invalid page number
        res6b = self.testapp.get(
            '/dashboard/foo/bar/baz',
            status=200,
        )

        self.failUnless(
            '<p>Number of data sets:' in res6b.body)

        # change the number of items to show
        form = res6b.forms[1]
        form['num_to_show'] = "42"  # post a number: OK
        resX = form.submit('submit', status=200)

        form = resX.forms[1]
        form['num_to_show'] = "mooo"  # post a string: no good
        resY = form.submit('submit', status=200)

        #import pdb; pdb.set_trace()
        # member details
        #
        # now look at some members details with nonexistant id
        res7 = self.testapp.get('/detail/5000', status=302)
        res7a = res7.follow()
        res7a = res7a.follow()
        self.failUnless('Dashboard' in res7a.body)

        # now look at some members details
        res7 = self.testapp.get('/detail/1', status=200)
        self.failUnless('Firstnäme' in res7.body)
        self.failUnless(
            "<td>signature received?</td><td>No</td>" in res7.body)
        self.failUnless(
            "<td>payment received?</td><td>No</td>" in res7.body)

        form = res7.form
        form['signature_received'] = True
        form['payment_received'] = True
        res8 = form.submit('submit')
        #print(res8.body)
        self.failUnless(
            "<td>signature received?</td><td>True</td>" in res8.body)
        self.failUnless(
            "<td>payment received?</td><td>True</td>" in res8.body)
        ################################################################
        # now we change some of the details: switch signature status
        # via http-request rather than the form
        resD1 = self.testapp.get('/detail/1', status=200)  # look at details
        self.assertTrue(
            "<td>signature received?</td><td>True</td>" in resD1.body)
        self.assertTrue(
            "<td>payment received?</td><td>True</td>" in resD1.body)
        #
        # switch signature
        resD2a = self.testapp.get('/switch_sig/1', status=302)  # # # # # OFF
        resD2b = resD2a.follow()  # we are taken to the dashboard
        resD2b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "<td>signature received?</td><td>No</td>" in resD2b.body)
        resD2a = self.testapp.get('/switch_sig/1', status=302)  # # # # # ON
        resD2b = resD2a.follow()  # we are taken to the dashboard
        resD2b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "<td>signature received?</td><td>True</td>" in resD2b.body)
        #
        # switch payment
        resD3a = self.testapp.get('/switch_pay/1', status=302)  # # # # OFF
        resD3b = resD3a.follow()  # we are taken to the dashboard
        resD3b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "<td>payment received?</td><td>No</td>" in resD3b.body)
        resD3a = self.testapp.get('/switch_pay/1', status=302)  # # # # ON
        resD3b = resD3a.follow()  # we are taken to the dashboard
        resD3b = self.testapp.get('/detail/1', status=200)
        self.assertTrue(
            "<td>payment received?</td><td>True</td>" in resD3b.body)
        #
        ####################################################################
        # delete an entry
        resDel1 = self.testapp.get('/dashboard/0/id/asc', status=200)

#        self.failUnless(
#            '      <p>Number of data sets: 1</p>' in resDel1.body.splitlines())
        resDel2 = self.testapp.get('/delete/1', status=302)
        resDel3 = resDel2.follow()
        resDel3 = resDel3.follow()
        self.failUnless('was deleted' in resDel3.body)

        # finally log out ##################################################
        res9 = self.testapp.get('/logout', status=302)  # redirects to login
        res10 = res9.follow()
        self.failUnless('login' in res10.body)

    def test_dashboard_orderByIdAsc_dashboardOrdered(self):
        res = self._login()
        res2 = self.testapp.get('/dashboard/0/id/asc')
        pq = self._get_pyquery(res2.body)
        # column-order: id code firstname lastname
        first_member_row = pq('tr:nth-child(2)')
        id_ = first_member_row('td:nth-child(1)')
        self.assertEqual('1', id_.text())

    def test_dashboard_orderByIdDesc_dashboardOrdered(self):
        res = self._login()
        res2 = self.testapp.get('/dashboard/0/id/desc')
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        id_ = first_member_row('td:nth-child(1)')
        self.assertEqual('3', id_.text())

    def test_dashboard_orderByFirstnameAsc_dashboardOrdered(self):
        res = self._login()
        res2 = self.testapp.get('/dashboard/0/firstname/asc')
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        first_name = first_member_row('td:nth-child(3)')
        self.assertEqual(u'AAASomeFirstnäme', first_name.text())

    def test_dashboard_orderByFirstnameDesc_dashboardOrdered(self):
        res = self._login()
        res2 = self.testapp.get('/dashboard/0/firstname/desc')
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        first_name = first_member_row('td:nth-child(3)')
        self.assertEqual(u'SomeFirstnäme', first_name.text())

    def test_dashboard_orderByLastnameAsc_dashboardOrdered(self):
        res = self._login()
        res2 = self.testapp.get('/dashboard/0/lastname/asc')
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(4)')
        self.assertEqual(u'AAASomeLastnäme', last_name.text())

    def test_dashboard_orderByLastnameDesc_dashboardOrdered(self):
        self._login()
        res2 = self.testapp.get('/dashboard/0/lastname/desc')
        pq = self._get_pyquery(res2.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(4)')
        self.assertEqual(u'XXXSomeLastnäme', last_name.text())

    def test_dashboard_afterDelete_sameOrderAsBefore(self):
        self._login()
        self.testapp.get('/dashboard/0/lastname/asc')  # To set cookie with order and orderby
        resdel = self.testapp.get('/delete/3')  # Delete member with lastname AAASomeLastnäme
        resdel = resdel.follow()
        resdel = resdel.follow()
        pq = self._get_pyquery(resdel.body)
        first_member_row = pq('tr:nth-child(2)')
        last_name = first_member_row('td:nth-child(4)')
        self.assertEqual(u'SomeLastnäme', last_name.text())

    def test_dashboard_afterDelete_messageShown(self):
        self._login()
        resdel = self.testapp.get('/delete/1')
        resdel = resdel.follow()
        resdel = resdel.follow()
        pq = self._get_pyquery(resdel.body)
        message = pq('#message').text()
        self.assertTrue('was deleted' in message)

    def test_dashboard_onFirstPage_noPreviousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.testapp.get('/dashboard/0/id/desc')
        pq = self._get_pyquery(res.body)
        self.assertTrue(len(pq("#navigate_previous")) == 0)

    def test_dashboard_onFirstPage_nextLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.testapp.get('/dashboard/0/id/desc')
        pq = self._get_pyquery(res.body)
        self.assertTrue(len(pq("#navigate_next")) == 1)

    def test_dashboard_onSomePage_nextPreviousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.testapp.get('/dashboard/1/id/desc')
        pq = self._get_pyquery(res.body)
        self.assertTrue(len(pq("#navigate_next")) == 1)
        self.assertTrue(len(pq("#navigate_previous")) == 1)

    def test_dashboard_onLastPage_previousLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.testapp.get('/dashboard/3/id/desc')
        pq = self._get_pyquery(res.body)
        self.assertTrue(len(pq("#navigate_previous")) == 1)

    def test_dashboard_onLastPage_noNextLinkShown(self):
        self._login()
        self._change_num_to_show("1")
        res = self.testapp.get('/dashboard/3/id/desc')
        pq = self._get_pyquery(res.body)
        self.assertTrue(len(pq("#navigate_next")) == 0)

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
        res3 = res3.follow()
        self.failUnless('Dashboard' in res3.body)
        return res3

    def _change_num_to_show(self, num_to_show="1"):
        res = self.testapp.get('/dashboard/0/id/desc')
        form = res.forms[1]
        form['num_to_show'] = num_to_show
        resX = form.submit('submit', status=200)
        return resX

    def test_dashboard_search_code(self):
        """
        load the dashboard and search for confirmation code
        """
        #
        # login
        #
        res3 = self._login()

        """
        we fill the confirmation code search form with a valid code,
        submit the form
        and check results
        """
        # try invalid code
        form = res3.forms[0]
        form['code_to_show'] = 'foo'
        res = form.submit()
        self.failUnless('Dashboard' in res.body)
        # now use existing code
        form = res.forms[0]
        form['code_to_show'] = 'ABCDEFGFOO'
        res = form.submit()
        self.failIf('Dashboard' in res.body)

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
        res3 = res3.follow()
        self.failUnless('Dashboard' in res3.body)

        """
        try to load a users PDF
        check size
        """
        # try invalid code
        pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
        self.failUnless('The resource was found at' in pdf.body)
        pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
        # now use existing code
        self.failUnless(80000 < len(pdf.body) < 150000)  # check pdf size

    def test_dashboard_mail_signature_confirmation(self):
        """
        load the dashboard and send out confirmation mails
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
        res3 = res3.follow()

        self.failUnless('Dashboard' in res3.body)

        """
        try to send out the signature confirmation email
        """
        # try invalid code
        pdf = self.testapp.get('/re_C3S_SCE_AFM_WRONGCODE.pdf')
        self.failUnless('The resource was found at' in pdf.body)
        pdf = self.testapp.get('/re_C3S_SCE_AFM_ABCDEFGFOO.pdf')
        # now use existing code
        self.failUnless(80000 < len(pdf.body) < 150000)  # check pdf size


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
            #print("removed old DBSession ===================================")
        except:
            #print("no DBSession to remove ==================================")
            pass
        try:
            os.remove('test_webtest_functional.db')
            #print "deleted old test database"
        except:
            pass
            #print "never mind"

        my_settings = {
            'sqlalchemy.url': 'sqlite:///test_webtest_functional.db',
            'available_languages': 'da de en es fr',
            'c3smembership.mailaddr': 'c@c3s.cc'}
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

        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        self.session.close()
        self.session.remove()
        os.remove('test_webtest_functional.db')

    def test_base_template(self):
        """load the front page, check string exists"""
        res = self.testapp.get('/', status=200)
        self.failUnless('Cultural Commons Collecting Society' in res.body)
        self.failUnless(
            'Copyright 2013, C3S SCE' in res.body)

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
        #print(res.body) #  if you want to see the pages source
        self.failUnless(
            'Mitgliedschaftsantrag für die' in res.body)
        self.failUnless(
            '<input type="hidden" name="_LOCALE_" value="de"' in res.body)

    def test_accept_language_header_en(self):
        """check the http 'Accept-Language' header obedience: english
        load the front page, check english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get(
            '/', status=200,
            headers={
                'Accept-Language': 'en'})
        #print(res.body) #  if you want to see the pages source
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
    #         'En envoyant un courriel à data@c3s.cc vous pouvez' in res.body)

    def test_no_cookies(self):
        """load the front page, check default english string exists"""
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get(
            '/', status=200,
            headers={
                'Accept-Language': 'af, cn'})  # ask for missing languages
        #print res.body
        self.failUnless('Application for Membership' in res.body)

#############################################################################
# check for validation stuff

    def test_form_lang_en_non_validating(self):
        """load the join form, check english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/?_LOCALE_=en', status=200)
        form = res.form
        #print(form.fields)
        #print(form.fields.values())
        form['firstname'] = 'John'
        #form['address2'] = 'some address part'
        res2 = form.submit('submit')
        self.failUnless(
            'There was a problem with your submission' in res2.body)

    def test_form_lang_de(self):
        """load the join form, check german string exists"""
        res = self.testapp.get('/?de', status=302)
        #print(res)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res2 = res.follow()
        #print(res2)
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
        #print(res1)
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
#        import pdb
#        pdb.set_trace()
            #'Your Email has been confirmed, Firstnäme Lastname!' in res.body)
        #res2 = self.testapp.get(
        #    '/C3S_SCE_AFM_Firstn_meLastname.pdf', status=200)
        #self.failUnless(len(res2.body) > 70000)

###########################################################################
# checking the disclaimer

    # def test_disclaimer_en(self):
    #     """load the disclaimer in english (via query_string),
    #     check english string exists"""
    #     res = self.testapp.reset()
    #     res = self.testapp.get('/disclaimer?en', status=302)
    #     self.failUnless('The resource was found at' in res.body)
    #     # we are being redirected...
    #     res1 = res.follow()
    #     self.failUnless(
    #         'you may order your data to be deleted at any time' in str(
    #             res1.body),
    #         'expected string was not found in web UI')

    # def test_disclaimer_de(self):
    #     """load the disclaimer in german (via query_string),
    #     check german string exists"""
    #     res = self.testapp.reset()
    #     res = self.testapp.get('/disclaimer?de', status=302)
    #     self.failUnless('The resource was found at' in res.body)
    #     # we are being redirected...
    #     res1 = res.follow()
    #     self.failUnless(
    #         'Datenschutzerkl' in str(
    #             res1.body),
    #         'expected string was not found in web UI')

    # def test_disclaimer_LOCALE_en(self):
    #     """load the disclaimer in english, check english string exists"""
    #     res = self.testapp.reset()
    #     res = self.testapp.get('/disclaimer?_LOCALE_=en', status=200)
    #     self.failUnless(
    #         'you may order your data to be deleted at any time' in str(
    #             res.body),
    #         'expected string was not found in web UI')

    # def test_disclaimer_LOCALE_de(self):
    #     """load the disclaimer in german, check german string exists"""
    #     res = self.testapp.reset()
    #     res = self.testapp.get('/disclaimer?_LOCALE_=de', status=200)
    #     self.failUnless(
    #         'Datenschutzerkl' in str(
    #             res.body),
    #         'expected string was not found in web UI')

    def test_success_wo_data_en(self):
        """load the success page in english (via query_string),
        check for redirection and english string exists"""
        res = self.testapp.reset()
        res = self.testapp.get('/success?en', status=302)
        self.failUnless('The resource was found at' in res.body)
        # we are being redirected...
        res1 = res.follow()
        #print(res1)
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
        #print(res1)
        self.failUnless(  # check text on page redirected to
            'Please fill out the form' in str(
                res1.body),
            'expected string was not found in web UI')

    # def test_success_w_data(self):
    #     """
    #     load the form, fill the form, (in one go via POST request)
    #     check for redirection, push button to send verification mail,
    #     check for 'mail was sent' message
    #     """
    #     res = self.testapp.reset()
    #     res = self.testapp.get('/', status=200)
    #     form = res.form
    #     print '*'*80
    #     print '*'*80
    #     print '*'*80
    #     print form.fields
    #     res = self.testapp.post(
    #         '/',  # where the form is served
    #         {
    #             'submit': True,
    #             'firstname': 'TheFirstName',
    #             'lastname': 'TheLastName',
    #             'date_of_birth': '1987-06-05',
    #             'address1': 'addr one',
    #             'address2': 'addr two',
    #             'postcode': '98765 xyz',
    #             'city': 'Devilstown',
    #             'country': 'AF',
    #             'email': 'email@example.com',
    #             'password': 'berries',
    #             'num_shares': '42',
    #             '_LOCALE_': 'en',
    #             #'activity': set(
    #             #    [
    #             #        u'composer',
    #             #        #u'dj'
    #             #    ]
    #             #),
    #             'invest_member': 'yes',
    #             'member_of_colsoc': 'yes',
    #             'name_of_colsoc': 'schmoo',
    #             #'opt_band': 'yes band',
    #             #'opt_URL': 'http://yes.url',
    #             #'noticed_dataProtection': 'yes'
    #             'num_shares': '23',
    #         },
    #         #status=302,  # expect redirection to success page
    #         status=200,  # expect redirection to success page
    #     )

    #     print(res.body)
    #     self.failUnless('The resource was found at' in res.body)
    #     # we are being redirected...
    #     res2 = res.follow()
    #     self.failUnless('Success' in res2.body)
    #     #print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    #     #print res2.body
    #     #print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
    #     self.failUnless('TheFirstName' in res2.body)
    #     self.failUnless('TheLastName' in res2.body)
    #     self.failUnless('1987-06-05' in res2.body)
    #     self.failUnless('addr one' in res2.body)
    #     self.failUnless('addr two' in res2.body)
    #     self.failUnless('Devilstown' in res2.body)
    #     self.failUnless('email@example.com' in res2.body)
    #     self.failUnless('schmoo' in res2.body)

    #     # now check for the "mail was sent" confirmation
    #     res3 = self.testapp.post(
    #         '/check_email',
    #         {
    #             'submit': True,
    #             'value': "send mail"
    #         }
    #     )
    #     #print(res3)
    #     self.failUnless(
    #         'An email was sent, TheFirstName TheLastName!' in res3.body)

#     def test_success_and_reedit(self):
#         """
#         submit form, check success, re-edit: are the values pre-filled?
#         """
#         res = self.testapp.reset()
#         res = self.testapp.get('/', status=200)
#         form = res.form
#         form['firstname'] = 'TheFirstNäme'
#         form['lastname'] = 'TheLastNäme'
#         form['address1'] = 'addr one'
#         form['address2'] = 'addr two'
#         res2 = form.submit('submit')
#         print res2.body
# #                'submit': True,
# #                'date_of_birth': '1987-06-05',
# #                'address2': 'addr two',
# #                'postcode': '98765 xyz',
# #                'city': 'Devilstöwn',
# #                'email': 'email@example.com',
# #                'num_shares': '23',
# #                '_LOCALE_': 'en',
# #                #'activity': set(
#                 #    [
#                 #        'composer',
#                 #        #u'dj'
#                 #    ]
#                 #),
# #                'country': 'AF',
# #                'membership_type': 'investing',
# #                'member_of_colsoc': 'yes',
# #                'name_of_colsoc': 'schmoö',
#                 #'opt_band': 'yes bänd',
#                 #'opt_URL': 'http://yes.url',
#                 #'noticed_dataProtection': 'yes'

# #            },
# #            status=302,  # expect redirection to success page
# #        )

    #    print(res.body)
    #     self.failUnless('The resource was found at' in res.body)
    #     # we are being redirected...
    #     res2 = res.follow()
    #     self.failUnless('Success' in res2.body)
    #     #print("success page: \n%s") % res2.body
    #     #self.failUnless(u'TheFirstNäme' in (res2.body))

    #     # go back to the form and check the pre-filled values
    #     res3 = self.testapp.get('/')
    #     #print(res3.body)
    #     #print("edit form: \n%s") % res3.body
    #     self.failUnless('TheFirstNäme' in res3.body)
    #     form = res3.form
    #     self.failUnless(form['firstname'].value == u'TheFirstNäme')

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
        #print res2.body
        self.failUnless("Load your PDF..." in res2.body)
        self.failUnless(
            "/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf" in res2.body)
        # load the PDF, check size
        res3 = self.testapp.get(
            '/C3S_SCE_AFM_SomeFirstn_meSomeLastn_me.pdf',
            status=200
        )
        #print("length of result: %s") % len(res3.body)
        #print("body result: %s") % (res3.body)  # ouch, PDF content!
        self.failUnless(80000 < len(res3.body) < 150000)  # check pdf size

    def test_email_confirmation_wrong_mail(self):
        """
        test email confirmation with a wrong email
        """
        res = self.testapp.reset()
        res = self.testapp.get(
            '/verify/NOTEXISTS@shri.de/ABCDEFGHIJ', status=200)
        #print(res.body)
        self.failUnless("Please enter your password." in res.body)
        # XXX this test shows nothing interesting

    def test_email_confirmation_wrong_code(self):
        """
        test email confirmation with a wrong code
        """
        res = self.testapp.reset()
        res = self.testapp.get('/verify/foo@shri.de/WRONGCODE', status=200)
        #print(res.body)
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

