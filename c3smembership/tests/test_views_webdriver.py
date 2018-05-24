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
# from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER
from subprocess import call
import time
import unittest

from webdriver_utils import (
    Server,
    Client
)

LOGGER.setLevel(logging.WARNING)  # silence logging

"""
this setting controls whether the browser will be visible (1) or not (0)
"""
is_visible = 1

# configuration of testing framework
cfg = {
    'app': {
        'host': '0.0.0.0',
        'port': '6543',
        'db': 'webdrivertest.db',
        'ini': "webdrivertest.ini",
        'appSettings': {},
    },
}
server = Server()
client = Client()


class SeleniumTestBase(unittest.TestCase):

    # overload: configuration of individual appSettings
    @classmethod
    def appSettings(self):
        return {}

    def initialize_db(self):
        """
        make sure we have entries in the DB
        """
        if os.path.isfile('webdrivertest.db'):
            call(['rm', 'webdrivertest.db'])
            print("old database was deleted.")
        print("initialize the test database:")
        call(['env/bin/initialize_c3sMembership_db', 'webdrivertest.ini'])
        print("database was set up.")

    def setUp(self):
        # # daemon start/stop
        # # stop the daemon iff running
        # call(['env/bin/pserve', 'webdrivertest.ini', 'stop'])
        # # start the app
        # call(['env/bin/pserve', 'webdrivertest.ini', 'start'])

        # wsgi way!
        self.cfg = cfg

        self.srv = server.connect(
            cfg=self.cfg,
            customAppSettings=self.appSettings(),
            wrapper='StopableWSGIServer'
        )
        # self.cli = client.connect(
        #        cfg=self.cfg
        # )

        time.sleep(0.1)

        # self.display = Display(
        #     visible=is_visible,
        #     size=(1024, 768)
        #     # size=(1600, 1200)
        # )
        # self.display.start()
        # self.driver = webdriver.Firefox()
        self.driver = webdriver.PhantomJS()
        # self.driver = webdriver.Chrome()
        # get rid of all cookies
        self.driver.delete_all_cookies()

    def tearDown(self):
        self.driver.close()
        self.driver.quit()
        # self.display.stop()
        # client.disconnect()
        server.disconnect()
        time.sleep(2)


class JoinFormTests(SeleniumTestBase):
    """
    Test the join form with selenium/webdriver.
    """
    def setUp(self):
        super(JoinFormTests, self).setUp()

    def tearDown(self):
        # self.driver.quit()
        super(JoinFormTests, self).tearDown()
        # call(['env/bin/pserve', 'webdrivertest.ini', 'stop'])

    def test_form_submission_de(self):
        """
        A webdriver test for the join form, german version
        """
        self.assertEqual(self.driver.get_cookies(), [])
        # load the page with the form, choose german
        self.driver.get("http://0.0.0.0:6543?de")
        # self.driver.maximize_window()

        self.driver.get_screenshot_as_file('test_form_submission_de.png')
        self.failUnless(
            u'Mitgliedschaftsantrag' in self.driver.page_source)

        # check for cookie -- should be 'de' for germen
        self.assertEquals(self.driver.get_cookie('_LOCALE_')['value'], u'de')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        time.sleep(0.1)
        self.driver.find_element_by_name('email').send_keys('c@c3s.cc')
        time.sleep(0.1)
        self.driver.find_element_by_name('password').send_keys('foobar')
        time.sleep(0.1)
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        time.sleep(0.1)
        self.driver.find_element_by_name('address1').send_keys('addr one')
        time.sleep(0.11)
        self.driver.find_element_by_name('address2').send_keys('addr two')
        time.sleep(0.11)
        self.driver.find_element_by_name('postcode').send_keys('98765')
        time.sleep(0.1)
        self.driver.find_element_by_name('city').send_keys('townish')
        time.sleep(0.1)
        self.driver.find_element_by_name('country').send_keys('Gri')
        time.sleep(0.1)
        self.driver.find_element_by_name('year').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('year').send_keys('1998')
        time.sleep(0.1)
        self.driver.find_element_by_name('month').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('month').send_keys('12')
        time.sleep(0.1)
        self.driver.find_element_by_name('day').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('day').send_keys('12')
        time.sleep(0.1)
        self.driver.find_element_by_name('membership_type').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('other_colsoc').click()  # Yes
        # self.driver.find_element_by_id('other_colsoc-1').click()  # No
        time.sleep(0.1)
        self.driver.find_element_by_id('colsoc_name').send_keys('GEMA')
        time.sleep(0.1)
        self.driver.find_element_by_name('got_statute').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('got_dues_regulations').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('privacy_consent').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('num_shares').send_keys('7')

        self.driver.find_element_by_name('submit').click()

        self.failUnless(
            u'Bestätigungs-E-Mail schicken' in self.driver.page_source)

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

        time.sleep(1)  # wait a little
        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@c3s.cc')
        # self.assertEqual(self.driver.find_element_by_name(
        #    'password').get_attribute('value'), 'foobar')
        # print("the password: %s" % self.driver.find_element_by_name(
        #        'password').get_attribute('value'))
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
        self.driver.find_element_by_id('other_colsoc-1').click()  # No colsoc
        self.driver.find_element_by_id(
            'colsoc_name').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_id('colsoc_name').send_keys(Keys.DELETE)
        # enter password
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        time.sleep(0.1)

        self.driver.find_element_by_name('submit').click()
        time.sleep(0.1)
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)
        # print self.driver.page_source
        # time.sleep(10)

        self.driver.find_element_by_name('send_email').click()
        time.sleep(0.1)

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
        self.driver.get("http://0.0.0.0:6543?en")
        # self.driver.maximize_window()

        self.driver.get_screenshot_as_file('test_form_submission_en.png')

        self.failUnless(  # english !?!
            u'Application for Membership' in self.driver.page_source)

        # check for cookie -- should be 'en' for english
        self.assertEquals(self.driver.get_cookie('_LOCALE_')['value'], u'en')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        time.sleep(0.1)
        self.driver.find_element_by_name('email').send_keys('c@c3s.cc')
        time.sleep(0.1)
        self.driver.find_element_by_name('password').send_keys('foobar')
        time.sleep(0.1)
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        time.sleep(0.1)
        self.driver.find_element_by_name('address1').send_keys('addr one')
        time.sleep(0.11)
        self.driver.find_element_by_name('address2').send_keys('addr two')
        time.sleep(0.11)
        self.driver.find_element_by_name('postcode').send_keys('98765')
        time.sleep(0.1)
        self.driver.find_element_by_name('city').send_keys('townish')
        time.sleep(0.1)
        self.driver.find_element_by_name('country').send_keys('Gro')
        time.sleep(0.1)
        self.driver.find_element_by_name('year').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('year').send_keys('1998')
        time.sleep(0.1)
        self.driver.find_element_by_name('month').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('month').send_keys('12')
        time.sleep(0.1)
        self.driver.find_element_by_name('day').send_keys(Keys.CONTROL, "a")
        self.driver.find_element_by_name('day').send_keys('12')
        time.sleep(0.1)
        self.driver.find_element_by_name('membership_type').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('other_colsoc').click()  # Yes
        # self.driver.find_element_by_id('other_colsoc-1').click()  # No
        time.sleep(0.1)
        self.driver.find_element_by_id('colsoc_name').send_keys('GEMA')
        time.sleep(0.1)
        self.driver.find_element_by_name('got_statute').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('got_dues_regulations').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('privacy_consent').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('num_shares').send_keys('7')

        self.driver.find_element_by_name('submit').click()

        # self.failUnless('E-Mail anfordern' in self.driver.page_source)
        self.failUnless('Send verification email' in self.driver.page_source)

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
        time.sleep(1)  # wait a little
        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@c3s.cc')
        # self.assertEqual(self.driver.find_element_by_name(
        #    'password').get_attribute('value'), 'foobar')
        # print("the password: %s" % self.driver.find_element_by_name(
        #        'password').get_attribute('value'))
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
        self.driver.find_element_by_id('other_colsoc-1').click()  # No colsoc
        self.driver.find_element_by_id('colsoc_name').send_keys('')
        # enter password
        self.driver.find_element_by_name('password').send_keys('foobar')
        self.driver.find_element_by_name('password-confirm').send_keys(
            'foobar')
        time.sleep(0.1)

        self.driver.find_element_by_name('submit').click()
        time.sleep(0.1)
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)
        # print self.driver.page_source
        # time.sleep(10)

        self.driver.find_element_by_name('send_email').click()
        time.sleep(0.1)

        page = self.driver.page_source

        # self.assertTrue('C3S Mitgliedsantrag: Bitte Emails abrufen.' in page)
        self.assertTrue('C3S Membership Application: Check your email' in page)
        # self.assertTrue('Eine Email wurde verschickt,' in page)
        self.assertTrue('An email was sent,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        # self.assertTrue(
        #    u'Du wirst eine Email von noreply@c3s.cc mit einem ' in page)
        # self.assertTrue(
        #    u'Bestätigungslink erhalten. Bitte rufe Deine Emails ab.' in page)
        self.assertTrue(
            u'You will receive an email from noreply@c3s.cc with ' in page)
        self.assertTrue(
            u'a link. Please check your email!' in page)

        # self.assertTrue(u'Der Betreff der Email lautet:' in page)
        self.assertTrue(u'The email subject line will read:' in page)
        # self.assertTrue(u'C3S: Email-Adresse' in page)
        self.assertTrue(u'C3S: confirm your email address ' in page)
        # self.assertTrue(u'tigen und Formular abrufen.' in page)
        self.assertTrue(u'and load your PDF' in page)
        time.sleep(0.1)


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
        # self.driver.quit()
        super(EmailVerificationTests, self).tearDown()
        # call(['env/bin/pserve', 'webdrivertest.ini', 'stop'])

    def test_verify_email_de(self):  # views.py 296-298
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        url = "http://0.0.0.0:6543/verify/uat.yes@c3s.cc/ABCDEFGHIJ?de"
        self.driver.get(url)

        # print(self.driver.page_source)
        self.assertTrue(
            u'Bitte gib Dein Passwort ein, um' in self.driver.page_source)
        self.assertTrue(
            u'Deine E-Mail-Adresse zu bestätigen.' in self.driver.page_source)
        self.assertTrue(
            'Hier geht es zum PDF...' in self.driver.page_source)

        # try with empty or wrong password -- must fail
        self.driver.find_element_by_name(
            'password').send_keys('')  # empty password
        self.driver.find_element_by_name('submit').click()

        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)

        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)
        self.driver.find_element_by_name(
            'password').send_keys('schmoo')  # wrong password
        self.driver.find_element_by_name('submit').click()

        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)
        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)

        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.driver.find_element_by_name('submit').click()

        # print(self.driver.page_source)
        self.assertTrue('Lade Dein PDF...' in self.driver.page_source)
        self.assertTrue(
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)
        # XXX TODO: check PDF download

    def test_verify_email_en(self):  # views.py 296-298
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        url = "http://0.0.0.0:6543/verify/uat.yes@c3s.cc/ABCDEFGHIJ?en"
        self.driver.get(url)

        # print(self.driver.page_source)
        # check text on page
        self.assertTrue(
            'Please enter your password in order ' in self.driver.page_source)
        self.assertTrue(
            'to verify your email address.' in self.driver.page_source)

        #
        # enter empty or wrong password -- must fail
        self.driver.find_element_by_name(
            'password').send_keys('')  # empty password
        self.driver.find_element_by_name('submit').click()  # submit

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        self.driver.find_element_by_name(
            'password').send_keys('schmoo')  # wrong password
        self.driver.find_element_by_name('submit').click()  # submit

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        #
        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.driver.find_element_by_name('submit').click()  # submit

        # print(self.driver.page_source)
        self.assertTrue('Load your PDF...' in self.driver.page_source)
        self.assertTrue(  # PDF form is visible
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)
        # XXX TODO: check PDF download
