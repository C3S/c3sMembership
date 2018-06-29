# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.share_repository package.
"""

import datetime
import re
import transaction
import unittest

from pyramid import testing
from sqlalchemy import engine_from_config
from sqlalchemy.sql import func
from webtest import TestApp

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.models import (
    C3sStaff,
    Group,
    C3sMember,
)


class MailerDummy(object):

    def __init__(self):
        self._email = None

    def send(self, email):
        self._email = email

    def get_email(self):
        return self._email


class GetMailerDummy(object):

    def __init__(self):
        self._mailer = MailerDummy()

    def __call__(self, request):
        return self._mailer


class DateTimeDummy(object):

    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


class MembershipApplicationTest(unittest.TestCase):

    def setUp(self):
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'api_auth_token': u"SECRETAUTHTOKEN",
            'c3smembership.url': u'localhost',
            'testing.mail_to_console': u'false',
        }
        self.config = testing.setUp()
        app = main({}, **my_settings)
        self.get_mailer = GetMailerDummy()
        app.registry.get_mailer = self.get_mailer
        app.registry.membership_application.datetime = DateTimeDummy(
            datetime.datetime(2018, 4, 26, 12, 23, 34))

        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

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

        self.testapp = TestApp(app)

    def tearDown(self):
        testing.tearDown()
        DBSession.close()
        DBSession.remove()

    def _login(self):
        """
        Log into the membership backend
        """
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res = form.submit('submit', status=302)

    def _validate_dashboard_redirect(self, res):
        """
        Validate that res is redirecting to the dashboard
        """
        res = res.follow()  # being redirected to dashboard with parameters
        self.__validate_dashboard(res)

    def _validate_dashboard(self, res):
        """
        Validate that res is the dashboard
        """
        self.failUnless('Dashboard' in res.body)

    @classmethod
    def _response_to_bare_text(cls, res):
        html = res.normal_body
        # remove JavaScript
        html = re.sub(re.compile('<script.*</script>'), '', html)
        # remove all tags
        html = re.sub(re.compile('<.*?>'), '', html)
        # remove html characters like &nbsp;
        html = re.sub(re.compile('&[A-Za-z]+;'), '', html)
        return html

    def test_membership_application(self):
        """
        Test the membership application process.

         1. Enter applicant data to application form
         2. Verify entered data and confirm
         3. Verify sent confirmation email
         4. Confirm email address via confirmation link
         5. Login to backend
         6. Verify applicant's detail page
         7. Set payment received
         8. Set signature received
         9. Make member
        10. Verify member details
        """
        self.testapp.reset()

        # 1. Enter applicant data to application form
        res = self.testapp.get('/', status=200)
        properties = {
            'firstname': u'Sönke',
            'lastname': u'Blømqvist',
            'email': u'soenke@example.com',
            'address1': u'℅ Big Boss',
            'address2': u'Håkanvägen 12',
            'postcode': u'ABC1234',
            'city': u'Stockholm',
            'year': u'1980',
            'month': u'01',
            'day': u'02',
            'name_of_colsoc': u'Svenska Tonsättares Internationella Musikbyrå',
            'num_shares': u'15',
            'password': u'worst password ever chosen',
            'password-confirm': u'worst password ever chosen',
        }
        for key, value in properties.iteritems():
            res.form[key] = value
        res.form['country'].select(text=u'Sweden')
        res.form['membership_type'].value__set(u'normal')
        res.form['other_colsoc'].value__set(u'yes')
        res.form['got_statute'].checked = True
        res.form['got_dues_regulations'].checked = True
        res.form['privacy_consent'].checked = True
        res = res.form.submit(u'submit', status=302)
        res = res.follow()

        # 2. Verify entered data and confirm
        body = self._response_to_bare_text(res)
        self.assertTrue('First Name: Sönke' in body)
        self.assertTrue('Last Name: Blømqvist' in body)
        self.assertTrue('Email Address: soenke@example.com' in body)
        self.assertTrue('Address Line 1: ℅ Big Boss' in body)
        self.assertTrue('Address Line 2: Håkanvägen 12' in body)
        self.assertTrue('Postal Code: ABC1234' in body)
        self.assertTrue('City: Stockholm' in body)
        self.assertTrue('Country: SE' in body)
        self.assertTrue('Date of Birth: 1980-01-02' in body)
        self.assertTrue('Type of Membership:normal' in body)
        self.assertTrue('Member of other Collecting Society: yes' in body)
        self.assertTrue('Membership(s): Svenska Tonsättares Internationella Musikbyrå' in body)
        self.assertTrue('Number of Shares: 15' in body)
        self.assertTrue('Cost of Shares (50 € each): 750 €' in body)
        res = self.testapp.get('/check_email', status=200)

        # 3. Verify sent confirmation email
        mailer = self.get_mailer(None)
        email = mailer.get_email()
        self.assertEqual(email.recipients, ['soenke@example.com'])
        self.assertEqual(email.subject, 'C3S: confirm your email address and load your PDF')

        # 4. Confirm email address via confirmation link
        match = re.search(
            'localhost(?P<url>[^\s]+)',
            email.body)

        self.assertTrue(match is not None)
        res = self.testapp.get(
            match.group('url'),
            status=200)

        self.assertTrue(u'password in order to verify your email' in res.body)
        res.form['password'] = 'worst password ever chosen'
        res = res.form.submit(u'submit', status=200)

        # 5. Login to backend
        self.testapp.reset()
        self._login()

        # 6. Verify applicant's detail page
        member_id = DBSession.query(func.max(C3sMember.id)).scalar()
        res = self.testapp.get('/detail/{0}'.format(member_id), status=200)

        body = self._response_to_bare_text(res)
        self.assertTrue('Firstname Sönke' in body)
        self.assertTrue('Lastname Blømqvist' in body)
        self.assertTrue('Email address soenke@example.com' in body)
        self.assertTrue('Email address confirmed Yes' in body)
        self.assertTrue('Address line 1 ℅ Big Boss' in body)
        self.assertTrue('Address line 2 Håkanvägen 12' in body)
        self.assertTrue('Postcode ABC1234' in body)
        self.assertTrue('City Stockholm' in body)
        self.assertTrue('Country SE' in body)
        self.assertTrue('Date of birth 1980-01-02' in body)
        self.assertTrue('Membership accepted  No' in body)
        self.assertTrue('Entity type Natural person' in body)
        self.assertTrue('Membership type normal' in body)
        self.assertTrue('Member of collecting societies Yes Svenska Tonsättares Internationella Musikbyrå' in body)
        self.assertTrue('Date of submission' in body)
        self.assertTrue('Signature received    No' in body)
        self.assertTrue('Signature confirmed No' in body)
        self.assertTrue('Payment received   No' in body)
        self.assertTrue('Payment confirmed No' in body)
        self.assertTrue('Shares  Total: 15' in body)
        # TODO:
        # - code
        # - locale, set explicitly and test both German and English
        # - date of submission

        # 7. Set payment received
        res = self.testapp.get(
            '/switch_pay/{0}'.format(member_id),
            headers={'Referer': 'asdf'},
            status=302)
        res = res.follow()
        body = self._response_to_bare_text(res)
        self.assertTrue('Payment received    Yes' in body)
        self.assertTrue('Payment reception date 2018-04-26 12:23:34' in body)

        # 8. Set signature received
        res = self.testapp.get(
            '/switch_sig/{0}'.format(member_id),
            headers={'Referer': 'asdf'},
            status=302)
        res = res.follow()
        body = self._response_to_bare_text(res)
        self.assertTrue('Signature received    Yes' in body)
        self.assertTrue('Signature reception date 2018-04-26 12:23:34' in body)

        # 9. Make member
        res = self.testapp.get(
            '/make_member/{0}'.format(member_id),
            headers={'Referer': 'asdf'},
            status=200)
        res.form['membership_date'] = '2018-04-27'
        res = res.form.submit('submit', status=302)
        res = res.follow()

        # 10. Verify member details
        membership_number = C3sMember.get_next_free_membership_number() - 1
        body = self._response_to_bare_text(res)
        self.assertTrue('Membership accepted  Yes' in body)
        self.assertTrue(
            'Membership number  {0}'.format(membership_number) in body)
        self.assertTrue('Membership date 2018-04-27' in body)
        self.assertTrue('Shares  Total: 15' in body)
        self.assertTrue('1 package(s)' in body)
        self.assertTrue('15 shares   (2018-04-27)' in body)
