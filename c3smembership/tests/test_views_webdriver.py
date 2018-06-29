# _*_ coding: utf-8 _*_
"""
These tests test

* the join form and
* the email verification form

using selenium/webdriver (make a browser do things), see:

* http://docs.seleniumhq.org/docs/
  03_webdriver.jsp#introducing-the-selenium-webdriver-api-by-example
* http://selenium-python.readthedocs.org/en/latest/api.html
* http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html

On the machine where these tests run, a virtual screen (X) must be running,
e.g. Xvfb, so the browser can start and things be done,
even in headless mode, e.g. on a virtual machine on a remote server
with no real screen attached.

While developing these tests, it comes in handy to have Xephyr installed,
a nested X server, so you see what is going on:
selenium/webdriver makes the browser do things.
"""

import logging
import os
from subprocess import call
import unittest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER
from webdriver_utils import Server


LOGGER.setLevel(logging.WARNING)

# this setting controls whether the browser will be visible (1) or not (0)
IS_VISIBLE = 1

# configuration of testing framework
CFG = {
    'app': {
        'host': '0.0.0.0',
        'port': '6544',
        'db': 'webdrivertest.db',
        'ini': "webdrivertest.ini",
        'appSettings': {},
    },
}
SERVER = Server()


class SeleniumTestBase(unittest.TestCase):
    """
    Base class for Selenium test cases
    """

    @classmethod
    def app_settings(cls):
        """
        Base method for application settings, can be overloaded when inherited
        """
        return {}

    @classmethod
    def initialize_db(cls):
        """
        make sure we have entries in the DB
        """
        if os.path.isfile('webdrivertest.db'):
            call(['rm', 'webdrivertest.db'], stdout=open(os.devnull, 'w'))
        call(
            ['env/bin/initialize_c3sMembership_db', 'webdrivertest.ini'],
            stdout=open(os.devnull, 'w'))

    def setUp(self):
        self.cfg = CFG
        self.srv = SERVER.connect(
            cfg=self.cfg,
            customAppSettings=self.app_settings(),
            wrapper='StopableWSGIServer'
        )

        self.driver = webdriver.PhantomJS()
        self.driver.delete_all_cookies()

    def tearDown(self):
        self.driver.close()
        self.driver.quit()
        SERVER.disconnect()


class JoinFormTests(SeleniumTestBase):
    """
    Test the join form with selenium/webdriver.
    """
    def setUp(self):
        super(JoinFormTests, self).setUp()

    def tearDown(self):
        super(JoinFormTests, self).tearDown()

    def test_form_submission_de(self):
        """
        A webdriver test for the join form, German version
        """
        self.assertEqual(self.driver.get_cookies(), [])
        # load the page with the form, choose german
        self.driver.get("http://0.0.0.0:6544?de")

        self.failUnless(
            u'Mitgliedschaftsantrag' in self.driver.page_source)

        # check for cookie -- should be 'de' for germen
        self.assertEquals(self.driver.get_cookie('_LOCALE_')['value'], u'de')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        self.driver.find_element_by_name('email').send_keys('c@c3s.cc')
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        self.driver.find_element_by_name('address1').send_keys('addr one')
        self.driver.find_element_by_name('address2').send_keys('addr two')
        self.driver.find_element_by_name('postcode').send_keys('98765')
        self.driver.find_element_by_name('city').send_keys('townish')
        self.driver.find_element_by_name('country').send_keys('Gri')
        self.driver.find_element_by_name('year').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('year').send_keys('1998')
        self.driver.find_element_by_name('month').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('month').send_keys('12')
        self.driver.find_element_by_name('day').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('day').send_keys('12')
        self.driver.find_element_by_name('membership_type').click()
        self.driver.find_element_by_name('other_colsoc').click()  # Yes
        self.driver.find_element_by_id('colsoc_name').send_keys('GEMA')
        self.driver.find_element_by_name('got_statute').click()
        self.driver.find_element_by_name('got_dues_regulations').click()
        self.driver.find_element_by_name('privacy_consent').click()
        self.driver.find_element_by_name('num_shares').send_keys('7')

        self.driver.find_element_by_name('submit').click()

        self.driver.get_screenshot_as_file('test_form_submission_de.png')
        self.failUnless(
            u'Nach Anfordern der Bestätigungsmail' in self.driver.page_source)

        # TODO: check contents of success page XXX
        self.assertTrue('Christoph' in self.driver.page_source)
        self.assertTrue('Scheid' in self.driver.page_source)
        self.assertTrue('Was nun passieren muss: Kontrolliere die Angaben '
                        'unten,' in self.driver.page_source)
        # TODO: check case colsoc = no views.py 765-767
        # TODO: check save to DB/randomstring: views.py 784-865

        self.failUnless(u'Daten bearbeiten' in self.driver.page_source)

        # back to the form
        self.driver.find_element_by_name('edit').click()

        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@c3s.cc')
        self.assertEqual(self.driver.find_element_by_name(
            'address1').get_attribute('value'), 'addr one')
        self.assertEqual(self.driver.find_element_by_name(
            'address2').get_attribute('value'), 'addr two')
        self.assertEqual(self.driver.find_element_by_name(
            'postcode').get_attribute('value'), '98765')
        self.assertEqual(self.driver.find_element_by_name(
            'city').get_attribute('value'), 'townish')
        self.assertEqual(self.driver.find_element_by_name(
            'country').get_attribute('value'), 'GR')
        self.assertEqual(self.driver.find_element_by_name(
            'year').get_attribute('value'), '1998')
        self.assertEqual(self.driver.find_element_by_name(
            'month').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'day').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'membership_type').get_attribute('value'), 'normal')
        self.assertEqual(self.driver.find_element_by_name(
            'other_colsoc').get_attribute('value'), 'yes')
        self.assertEqual(self.driver.find_element_by_id(
            'colsoc_name').get_attribute('value'), 'GEMA')
        self.assertEqual(self.driver.find_element_by_name(
            'num_shares').get_attribute('value'), '17')
        # change a detail
        self.driver.find_element_by_name('address2').send_keys(' plus')
        # ok, all data checked, submit again
        self.driver.find_element_by_name('submit').click()

        self.assertTrue('Bitte beachten: Es gab Fehler. Bitte Eingaben unten '
                        'korrigieren.' in self.driver.page_source)

        # verify we have to theck this again
        self.driver.find_element_by_name('got_statute').click()
        self.driver.find_element_by_name('got_dues_regulations').click()
        self.driver.find_element_by_name('privacy_consent').click()
        self.driver.find_element_by_id('other_colsoc-1').click()
        self.driver.find_element_by_id(
            'colsoc_name').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_id('colsoc_name').send_keys(Keys.DELETE)
        # enter password
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')

        self.driver.find_element_by_name('submit').click()
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)

        self.driver.find_element_by_name('send_email').click()

        page = self.driver.page_source

        self.assertTrue('C3S Mitgliedsantrag: Bitte E-Mails abrufen.' in page)
        self.assertTrue('Eine E-Mail wurde verschickt,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        self.assertTrue(
            u'Du wirst eine E-Mail von noreply@c3s.cc mit einem ' in page)
        self.assertTrue(
            u'Bestätigungslink erhalten. Bitte rufe Deine E-Mails ab.' in page)

        self.assertTrue(u'Der Betreff der E-Mail lautet:' in page)
        self.assertTrue(u'C3S: E-Mail-Adresse' in page)
        self.assertTrue(u'tigen und Formular abrufen' in page)

    def test_form_submission_en(self):
        """
        A webdriver test for the join form, english version
        """
        self.assertEqual(self.driver.get_cookies(), [])
        # load the page with the form
        self.driver.get("http://0.0.0.0:6544?en")

        self.driver.get_screenshot_as_file('test_form_submission_en.png')

        self.failUnless(
            u'Application for Membership' in self.driver.page_source)

        # check for cookie -- should be 'en' for english
        self.assertEquals(self.driver.get_cookie('_LOCALE_')['value'], u'en')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        self.driver.find_element_by_name('email').send_keys('c@c3s.cc')
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        self.driver.find_element_by_name('address1').send_keys('addr one')
        self.driver.find_element_by_name('address2').send_keys('addr two')
        self.driver.find_element_by_name('postcode').send_keys('98765')
        self.driver.find_element_by_name('city').send_keys('townish')
        self.driver.find_element_by_name('country').send_keys('Gro')
        self.driver.find_element_by_name('year').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('year').send_keys('1998')
        self.driver.find_element_by_name('month').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('month').send_keys('12')
        self.driver.find_element_by_name('day').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('day').send_keys('12')
        self.driver.find_element_by_name('membership_type').click()
        # Yes
        self.driver.find_element_by_name('other_colsoc').click()
        self.driver.find_element_by_id('colsoc_name').send_keys('GEMA')
        self.driver.find_element_by_name('got_statute').click()
        self.driver.find_element_by_name('got_dues_regulations').click()
        self.driver.find_element_by_name('privacy_consent').click()
        self.driver.find_element_by_name('num_shares').send_keys('7')

        self.driver.find_element_by_name('submit').click()

        self.failUnless(
            'Click the button to have an email' in self.driver.page_source)

        # TODO: check contents of success page XXX
        self.assertTrue('Christoph' in self.driver.page_source)
        self.assertTrue('Scheid' in self.driver.page_source)
        self.assertTrue('What happens next: You need to check the information '
                        'below to be correct, receive an email to verify your '
                        'address,' in self.driver.page_source)

        # TODO: check case colsoc = no views.py 765-767
        # TODO: check save to DB/randomstring: views.py 784-865
        # TODO: check re-edit of form: views.py 877-880 XXX
        self.driver.find_element_by_name('edit').click()
        # back to the form
        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@c3s.cc')
        self.assertEqual(self.driver.find_element_by_name(
            'address1').get_attribute('value'), 'addr one')
        self.assertEqual(self.driver.find_element_by_name(
            'address2').get_attribute('value'), 'addr two')
        self.assertEqual(self.driver.find_element_by_name(
            'postcode').get_attribute('value'), '98765')
        self.assertEqual(self.driver.find_element_by_name(
            'city').get_attribute('value'), 'townish')
        self.assertEqual(self.driver.find_element_by_name(
            'country').get_attribute('value'), 'GR')
        self.assertEqual(self.driver.find_element_by_name(
            'year').get_attribute('value'), '1998')
        self.assertEqual(self.driver.find_element_by_name(
            'month').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'day').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'membership_type').get_attribute('value'), 'normal')
        self.assertEqual(self.driver.find_element_by_name(
            'other_colsoc').get_attribute('value'), 'yes')
        self.assertEqual(self.driver.find_element_by_id(
            'colsoc_name').get_attribute('value'), 'GEMA')
        self.assertEqual(self.driver.find_element_by_name(
            'num_shares').get_attribute('value'), '17')
        # change a detail
        self.driver.find_element_by_name('address2').send_keys(' plus')
        # ok, all data checked, submit again
        self.driver.find_element_by_name('submit').click()

        self.assertTrue('Please note: There were errors, please check the '
                        'form below.' in self.driver.page_source)

        # verify we have to theck this again
        self.driver.find_element_by_name('got_statute').click()
        self.driver.find_element_by_name('got_dues_regulations').click()
        self.driver.find_element_by_name('privacy_consent').click()
        self.driver.find_element_by_id('other_colsoc-1').click()
        self.driver.find_element_by_id('colsoc_name').send_keys('')
        # enter password
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')

        self.driver.find_element_by_name('submit').click()
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)

        self.driver.find_element_by_name('send_email').click()

        page = self.driver.page_source

        self.assertTrue('C3S Membership Application: Check your email' in page)
        self.assertTrue('An email was sent,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        self.assertTrue(
            u'You will receive an email from noreply@c3s.cc with ' in page)
        self.assertTrue(
            u'a link. Please check your email!' in page)

        self.assertTrue(u'The email subject line will read:' in page)
        self.assertTrue(u'C3S: confirm your email address ' in page)
        self.assertTrue(u'and load your PDF' in page)


class EmailVerificationTests(SeleniumTestBase):
    """
    Tests for the view where users are sent after submitting their data.
    They must enter their password and thereby confirm their email address,
    as they got to this form by clicking on a link supplied by mail.
    """

    def setUp(self):
        super(EmailVerificationTests, self).initialize_db()
        super(EmailVerificationTests, self).setUp()

    def tearDown(self):
        super(EmailVerificationTests, self).tearDown()

    def test_verify_email_de(self):
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        url = "http://0.0.0.0:6544/verify/uat.yes@c3s.cc/ABCDEFGHIJ?de"
        self.driver.get(url)

        self.assertTrue(
            u'Bitte gib Dein Passwort ein, um' in self.driver.page_source)
        self.assertTrue(
            u'Deine E-Mail-Adresse zu bestätigen.' in self.driver.page_source)
        self.assertTrue(
            'Hier geht es zum PDF...' in self.driver.page_source)

        # try with empty or wrong password -- must fail
        self.driver.find_element_by_name(
            'password').send_keys('')
        self.driver.find_element_by_name('submit').click()
        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)

        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)
        # wrong password
        self.driver.find_element_by_name(
            'password').send_keys('schmoo')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)
        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)

        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue('Lade Dein PDF...' in self.driver.page_source)
        self.assertTrue(
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)
        # XXX TODO: check PDF download

    def test_verify_email_en(self):
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        url = "http://0.0.0.0:6544/verify/uat.yes@c3s.cc/ABCDEFGHIJ?en"
        self.driver.get(url)

        # check text on page
        self.assertTrue(
            'Please enter your password in order ' in self.driver.page_source)
        self.assertTrue(
            'to verify your email address.' in self.driver.page_source)

        # enter empty or wrong password -- must fail
        # empty password
        self.driver.find_element_by_name(
            'password').send_keys('')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        # wrong password
        self.driver.find_element_by_name(
            'password').send_keys('schmoo')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue('Load your PDF' in self.driver.page_source)
        self.assertTrue(
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)
        # XXX TODO: check PDF download
