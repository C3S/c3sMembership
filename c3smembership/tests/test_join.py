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
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff
import c3smembership.utils as utils
import c3smembership.presentation.views.join as join
from c3smembership.presentation.views.join import (
    show_success,
    show_success_pdf,
    success_check_email,
    success_verify_email,
)


def encrypt_with_gnupg_dummy(data):
    return data


class DummyCallable(object):

    def __init__(self):
        self._args = None
        self._kwargs = None

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def get_args(self):
        return self._args

    def get_kwargs(self):
        return self._kwargs


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
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'test@example.com'
        self.config.registry.settings['c3smembership.status_receiver'] = \
            'test@example.com'
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

    def test_show_success_no_appstruct(self):
        self.config.add_route('join', '/')
        result = show_success(testing.DummyRequest())
        self.assertEqual(result.status_code, 302)

    def test_success_check_email_de(self):
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

        # Dependency injection to dirty way
        original_encrypt_with_gnupg = utils.encrypt_with_gnupg
        utils.encrypt_with_gnupg = encrypt_with_gnupg_dummy

        result = success_check_email(request)

        # Undo dependency injection
        utils.encrypt_with_gnupg = original_encrypt_with_gnupg

        self.assertTrue(result['lastname'] is 'bar')
        self.assertTrue(result['firstname'] is 'foo')

        # expect email to accountant and email to applicant for email address
        # confirmation
        self.assertEqual(len(mailer.outbox), 2)
        self.assertEqual(
            mailer.outbox[0].subject,
            '[C3S] Yes! a new member')
        self.assertEqual(
            mailer.outbox[1].subject,
            u'C3S: E-Mail-Adresse bestätigen und Formular abrufen')

        verif_link = "https://yes.c3s.cc/verify/bar@shri.de/"
        self.assertTrue("Hallo foo bar!" in mailer.outbox[1].body)
        self.assertTrue(verif_link in mailer.outbox[1].body)

    def test_success_check_email_en(self):
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
                'locale': 'en',
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

        # Dependency injection to dirty way
        original_encrypt_with_gnupg = utils.encrypt_with_gnupg
        utils.encrypt_with_gnupg = encrypt_with_gnupg_dummy

        result = success_check_email(request)
        self.assertTrue(result['lastname'] is 'bar')
        self.assertTrue(result['firstname'] is 'foo')

        # Undo dependency injection
        utils.encrypt_with_gnupg = original_encrypt_with_gnupg

        # expect email to accountant and email to applicant for email address
        # confirmation
        self.assertEqual(len(mailer.outbox), 2)
        self.assertEqual(
            mailer.outbox[0].subject,
            '[C3S] Yes! a new member')
        self.assertEqual(
            mailer.outbox[1].subject,
            'C3S: confirm your email address and load your PDF')

        verif_link = "https://yes.c3s.cc/verify/bar@shri.de/"
        self.assertTrue("Hello foo bar!" in mailer.outbox[1].body)
        self.assertTrue(verif_link in mailer.outbox[1].body)

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
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
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
        join.date = DummyDate(date(2018, 4, 29))
        form['year'] = u'2000'
        form['month'] = u'04'
        form['day'] = u'29'
        res = form.submit(u'submit', status=302)
        res = res.follow()
        self.assertTrue('information below to be correct' in res.body)

        # failure on test one day before 18th birthday
        res = self.testapp.get('/', status=200)
        form = self._fill_form_valid_natural(res.form)
        join.date = DummyDate(date(2018, 4, 29))
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

    def test_show_success_pdf(self):
        """
        Test the show_success_pdf method.show_success_pdf

        1. Generate PDF if appstruct is present
        2. Redirect if no appstruct is present
        """
        # 1. Generate PDF if appstruct is present
        self.config.add_route('join', '/')
        request = testing.DummyRequest()
        request.session['appstruct'] = {'test': 'dummy'}

        # Dependency injection the dirty way
        original_generate_pdf = join.generate_pdf
        generate_pdf = DummyCallable()
        join.generate_pdf = generate_pdf

        result = show_success_pdf(request)

        # Undo dependency injection
        join.generate_pdf = original_generate_pdf

        self.assertEqual(generate_pdf.get_args(), ({'test': 'dummy'},))

        # 2. Redirect if no appstruct is present
        self.config.add_route('join', '/')
        request = testing.DummyRequest()
        result = show_success_pdf(request)
        self.assertEqual('302 Found', result._status)
        self.assertEqual('http://example.com/', result.location)
