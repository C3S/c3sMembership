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
import glob
from subprocess import call
import time
from datetime import datetime
import unittest
import unicodedata
import re

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.remote_connection import LOGGER
from .webdriver_utils import Server
from selenium.webdriver.chrome.options import Options

LOGGER.setLevel(logging.WARNING)

# regex to match ascii
re_ascii = re.compile(r"[^A-Za-z0-9_.,-]")

# this setting controls whether the browser will be visible or not
options = Options()
options.headless = True

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


# Delete screenshots on each run of nosetests before the tests.
def delete_screenshots():
    """
    Deletes all screenshots of previous selenium tests.

    Deletes all `.png` files in the `./screenshot` folder.

    Returns:
        None.
    """
    if not int(os.environ.get("SELENIUM_SCREENSHOTS", 0)):
        return
    path = os.path.join('screenshots', '*.png')
    for screenshot in glob.glob(path):
        os.unlink(screenshot)


delete_screenshots()


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

        # Call initialize_c3sMembership_db from the environment. In case of
        # problems make sure the virtual environment is activated and
        # initialize_c3sMembership_db is found.
        call(
            ['initialize_c3sMembership_db', 'webdrivertest.ini'],
            stdout=open(os.devnull, 'w'))

    def setUp(self):
        self.cfg = CFG
        self.srv = SERVER.connect(
            cfg=self.cfg,
            customAppSettings=self.app_settings(),
            wrapper='StopableWSGIServer'
        )

        selenium_grid_url = os.environ.get("SELENIUM_GRID_URL", False)
        if selenium_grid_url:
            self.driver = webdriver.Remote(
                command_executor=selenium_grid_url, options=options)
            self.url = "http://%s:%s" % (
                os.environ.get("HOSTNAME", "server"), CFG['app']['port'])
        else:
            self.driver = webdriver.Chrome(options=options)
            self.url = "http://0.0.0.0:%s" % CFG['app']['port']
        self.driver.delete_all_cookies()
        # Sleep one second to let the webdriver initialize in order to try to
        # fix the issue that webdriver tests are breaking unpredictably on
        # the first get request.
        time.sleep(1)

    def tearDown(self):
        self.driver.close()
        self.driver.quit()
        SERVER.disconnect()

    def screenshot(self, name=''):
        """
        Takes a screenshot of the current browser client viewport.

        Screenshots may be switched on/off by envvar SELENIUM_SCREENSHOTS=1/0.

        Screenshots will be saved in `./screenshots`.
        The directory will be created, if it not exists.

        The filename will be a concatenation of:

        - time of execution
        - test classname
        - test method
        - name if provided

        Args:
            filename (Optional[str]): Additional name postfix for the file.
        """
        if not int(os.environ.get("SELENIUM_SCREENSHOTS", 0)):
            return
        # create path
        path = "screenshots"
        if not os.path.isdir(path):
            os.makedirs(path)
        # concat filename
        testtime = datetime.utcnow().strftime('%y%m%d.%H%M%S.%f')[:-4]
        testclass = self.__class__.__name__
        if testclass.startswith("Test"):
            testclass = testclass[4:]
        testmethod = self._testMethodName
        if testmethod.startswith("test_"):
            testmethod = testmethod[5:]
        testmethod = [word.title() for word in testmethod.split('_')]
        if testmethod and str(testmethod[0]).isnumeric():
            testmethod[0] += "-"
        testmethod = ''.join(testmethod)
        filename = [testtime, testclass, testmethod]
        if name:
            filename.append(name)
        filename = "-".join(filename)
        # sanitize filename (taken from werkzeug.utils.secure_filename)
        filename = unicodedata.normalize("NFKD", str(filename))
        filename = filename.encode("ascii", "ignore").decode("ascii")
        for sep in os.path.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, " ")
        filename = str(
            re_ascii.sub("", "_".join(filename.split()))
        ).strip("._-")
        # resize window
        original_size = self.driver.get_window_size()
        required_width = self.driver.execute_script(
            'return document.body.parentNode.scrollWidth')
        required_height = self.driver.execute_script(
            'return document.body.parentNode.scrollHeight')
        self.driver.set_window_size(required_width, required_height)
        # make screenshot
        self.driver.find_element_by_tag_name('body').screenshot(
            os.path.join(path, filename + '.png')
        )
        # reset window size
        self.driver.set_window_size(
            original_size['width'], original_size['height'])


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
        self.driver.get(self.url + "?de")
        self.screenshot("page-loaded")

        self.assertTrue(
            'Mitgliedschaftsantrag' in self.driver.page_source)

        # check for cookie -- should be 'de' for germen
        self.assertEqual(self.driver.get_cookie('_LOCALE_')['value'], 'de')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        self.driver.find_element_by_name('email').send_keys('c@example.com')
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

        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        self.assertTrue(
            'Nach Anfordern der Bestätigungsmail' in self.driver.page_source)

        # TODO: check contents of success page XXX
        self.assertTrue('Christoph' in self.driver.page_source)
        self.assertTrue('Scheid' in self.driver.page_source)
        self.assertTrue('Was nun passieren muss: Kontrolliere die Angaben '
                        'unten,' in self.driver.page_source)
        # TODO: check case colsoc = no views.py 765-767
        # TODO: check save to DB/randomstring: views.py 784-865

        # back to the form
        self.driver.find_element_by_id('back').click()
        self.screenshot("form-back")

        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@example.com')
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
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

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

        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)

        self.driver.find_element_by_id('next').click()
        self.screenshot("form-next")

        page = self.driver.page_source

        self.assertTrue('C3S Mitgliedsantrag: Bitte E-Mails abrufen.' in page)
        self.assertTrue('Eine E-Mail wurde verschickt,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        self.assertTrue('Du wirst eine E-Mail' in page)
        self.assertTrue('Bestätigungslink' in page)

        self.assertTrue('Der Betreff der E-Mail lautet:' in page)
        self.assertTrue('C3S: E-Mail-Adresse' in page)
        self.assertTrue('tigen und Formular abrufen' in page)

    def test_form_submission_en(self):
        """
        A webdriver test for the join form, english version
        """
        self.assertEqual(self.driver.get_cookies(), [])
        # load the page with the form
        self.driver.get(self.url + "?en")
        self.screenshot("page-loaded")

        self.assertTrue(
            'Application for Membership' in self.driver.page_source)

        # check for cookie -- should be 'en' for english
        self.assertEqual(self.driver.get_cookie('_LOCALE_')['value'], 'en')

        # fill out the form
        self.driver.find_element_by_name("firstname").send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        self.driver.find_element_by_name('email').send_keys('c@example.com')
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

        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        # self.driver.get_screenshot_as_file('test_form_submission_en.png')

        self.assertTrue(
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
        self.driver.find_element_by_id('back').click()
        self.screenshot("form-back")
        # back to the form
        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@example.com')
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
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

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

        self.screenshot("form-edited")
        self.driver.find_element_by_id('next').click()
        self.screenshot("form-sent")

        page = self.driver.page_source

        self.assertTrue('C3S Membership Application: Check your email' in page)
        self.assertTrue('An email was sent,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        self.assertTrue(
            'You will receive an email from us with ' in page)

        self.assertTrue('The email subject line will read:' in page)
        self.assertTrue('C3S: confirm your email address ' in page)
        self.assertTrue('and load your PDF' in page)


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
        url = self.url + "/verify/uat.yes@example.com/ABCDEFGHIJ?de"
        self.driver.get(url)
        self.screenshot("page-loaded")

        self.assertTrue(
            'Bitte gib Dein Passwort ein, um' in self.driver.page_source)
        self.assertTrue(
            'Deine E-Mail-Adresse zu bestätigen.' in self.driver.page_source)
        self.assertTrue(
            'Hier geht es zum PDF...' in self.driver.page_source)

        # try with empty or wrong password -- must fail
        self.driver.find_element_by_name(
            'password').send_keys('')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")
        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)

        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)
        # wrong password
        self.driver.find_element_by_name(
            'password').send_keys('schmoo')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)
        self.assertTrue('Hier geht es zum PDF...' in self.driver.page_source)

        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

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
        url = self.url + "/verify/uat.yes@example.com/ABCDEFGHIJ?en"
        self.driver.get(url)
        self.screenshot("page-loaded")

        # check text on page
        self.assertTrue(
            'Please enter your password in order ' in self.driver.page_source)
        self.assertTrue(
            'to verify your email address.' in self.driver.page_source)

        # enter empty or wrong password -- must fail
        # empty password
        self.driver.find_element_by_name(
            'password').send_keys('')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        # wrong password
        self.driver.find_element_by_name(
            'password').send_keys('schmoo')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        self.assertTrue(
            'Please enter your password.' in self.driver.page_source)

        # try correct password
        self.driver.find_element_by_name('password').send_keys('berries')
        self.screenshot("form-edited")
        self.driver.find_element_by_name('submit').click()
        self.screenshot("form-sent")

        self.assertTrue('Load your PDF' in self.driver.page_source)
        self.assertTrue(
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)
        # XXX TODO: check PDF download
