# -*- coding: utf-8 -*-
from datetime import (
    date,
    datetime,
)
import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from sqlalchemy import engine_from_config
import transaction
from webtest import TestApp

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.models import (
    C3sStaff,
    Group,
)
import c3smembership.views.afm as afm
from c3smembership.views.afm import (
    show_success,
    success_check_email,
    success_verify_email,
)


class DummyDate(object):

    def __init__(self, today):
        self._today = today

    def __call__(self, *args, **kwargs):
        return date(*args, **kwargs)

    def today(self):
        return self._today


class TestViews(unittest.TestCase):
    """
    very basic tests for the main views
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings[
            'c3smembership.url'] = 'https://yes.c3s.cc'
        self.config.registry.settings['c3smembership.mailaddr'] = 'c@c3s.cc'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.config.registry.get_mailer = get_mailer

        DBSession.remove()
        self.session = DBSession

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_show_success(self):
        """
        test the success page
        """
        self.config.add_route('join', '/')
        request = testing.DummyRequest(
            params={
                'appstruct': {
                    'firstname': 'foo',
                    'lastname': 'bar',
                }
            }
        )
        request.session['appstruct'] = {
            'person': {
                'firstname': 'foo',
                'lastname': 'bar',
            }
        }
        result = show_success(request)
        self.assertTrue(result['lastname'] is 'bar')
        self.assertTrue(result['firstname'] is 'foo')

    def test_success_check_email(self):
        """
        test the success_check_email view
        """
        self.config.add_route('join', '/')
        request = testing.DummyRequest(
            params={
                'appstruct': {
                    'firstname': 'foo',
                    'lastname': 'bar',
                }
            }
        )
        request.session['appstruct'] = {
            'person': {
                'firstname': 'foo',
                'lastname': 'bar',
                'email': 'bar@shri.de',
                'password': 'bad password',
                'address1': 'Some Street',
                'address2': '',
                'postcode': 'ABC123',
                'city': 'Stockholm',
                'country': 'SE',
                'locale': 'de',
                'date_of_birth': '1980-01-01',
            },
            'membership_info': {
                'membership_type': 'person',
                'member_of_colsoc': 'no',
                'name_of_colsoc': '',
                'privacy_consent': datetime(2018, 5, 24, 22, 16, 23),
            },
            'shares': {
                'num_shares': '3',
            },
        }
        mailer = get_mailer(request)
        result = success_check_email(request)
        self.assertTrue(result['lastname'] is 'bar')
        self.assertTrue(result['firstname'] is 'foo')

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject,
            'C3S: confirm your email address and load your PDF')

        verif_link = "https://yes.c3s.cc/verify/bar@shri.de/"
        self.assertTrue("Hallo foo bar!" in mailer.outbox[0].body)
        self.assertTrue(verif_link in mailer.outbox[0].body)

    def test_success_check_email_redirect(self):
        """
        test the success_check_email view redirection when appstruct is missing
        """
        self.config.add_route('join', '/')
        request = testing.DummyRequest()
        result = success_check_email(request)

        self.assertEqual('302 Found', result._status)
        self.assertEqual('http://example.com/', result.location)

    def _fill_form_valid_natural(self, form):
        form['firstname'] = u'SomeFirstname'
        form['lastname'] = u'SomeLastname'
        form['email'] = u'some@shri.de'
        form['password'] = u'jG2NVfOn0BroGrAXR7wy'
        form['password-confirm'] = u'jG2NVfOn0BroGrAXR7wy'
        form['address1'] = u"addr one"
        form['address2'] = u"addr two"
        form['postcode'] = u"12345"
        form['city'] = u"Footown Meeh"
        form['country'].value__set(u"DE")
        form['year'] = unicode(date.today().year-40)
        form['month'] = '1'
        form['day'] = '1'
        form['locale'] = u"DE"
        form['membership_type'].value__set(u'normal')
        form['other_colsoc'].value__set(u'no')
        form['name_of_colsoc'] = u"GEMA"
        form['num_shares'] = u'23'
        form['got_statute'].value__set(True)
        form['got_dues_regulations'].value__set(True)
        form['privacy_consent'].value__set(True)
        return form

    def test_join_c3s(self):
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
        with transaction.manager:
            accountants_group = Group(name=u"staff")
            DBSession.add(accountants_group)
            DBSession.flush()
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            DBSession.add(accountants_group)
            DBSession.add(staffer1)
            DBSession.flush()
        app = main({}, **my_settings)
        self.testapp = TestApp(app)

        # sucess for valid entry
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        res = form.submit(u'submit', status=302)
        res = res.follow()
        self.assertTrue('information below to be correct' in res.body)

        # success for 18th birthday
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        afm.date = DummyDate(date(2018, 4, 29))
        form['year'] = u'2000'
        form['month'] = u'04'
        form['day'] = u'29'
        res = form.submit(u'submit', status=302)
        res = res.follow()
        self.assertTrue('information below to be correct' in res.body)

        # failure on test one day before 18th birthday
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        afm.date = DummyDate(date(2018, 4, 29))
        form['year'] = u'2000'
        form['month'] = u'04'
        form['day'] = u'30'
        res = form.submit(u'submit', status=200)
        self.assertTrue('underaged person is currently not' in res.body)

        # failure for statute not checked
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        form['got_dues_regulations'].value__set(False)
        res = form.submit(u'submit', status=200)

        # failure for dues regulations not checked
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        form['got_dues_regulations'].value__set(False)
        res = form.submit(u'submit', status=200)

        # teardown
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    def test_success_verify_email(self):
        """
        test the success_verify_email view
        """
        self.config.add_route('join', '/')
        request = testing.DummyRequest()
        request.matchdict['email'] = 'foo@shri.de'
        request.matchdict['code'] = '12345678'
        result = success_verify_email(request)
        self.assertEqual(
            request.session.peek_flash('message_above_login'),
            [u'Please enter your password.'])
        self.assertEqual(result['result_msg'], 'something went wrong.')
        self.assertEqual(result['firstname'], '')
        self.assertEqual(result['lastname'], '')
        self.assertEqual(result['post_url'], '/verify/foo@shri.de/12345678')
        self.assertEqual(result['namepart'], '')
        self.assertEqual(result['correct'], False)
