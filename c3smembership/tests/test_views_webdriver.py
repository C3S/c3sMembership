# _*_ coding: utf-8 _*_
import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
# available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC
# available since 2.26.0
import time
from subprocess import call

# maybe check https://pypi.python.org/pypi/z3c.webdriver


class SeleniumTestBase(unittest.TestCase):
    def setUp(self):
        call(['env/bin/pserve', 'development.ini', 'start'])
        time.sleep(3)
        self.driver = webdriver.Firefox()  # PhantomJS()


class JoinFormTests(SeleniumTestBase):
    """
    test the join form using selenium (make a browser do things)
    see
    http://docs.seleniumhq.org/docs/03_webdriver.jsp
           #introducing-the-selenium-webdriver-api-by-example
    http://selenium-python.readthedocs.org/en/latest/api.html
    http://selenium.googlecode.com/svn/trunk/docs/api/py/index.html
    """
    def setUp(self):
        super(JoinFormTests, self).setUp()

    def tearDown(self):
        self.driver.quit()
        call(['env/bin/pserve', 'development.ini', 'stop'])

    def test_form_submission_de(self):
        from c3smembership.views import join_c3s  # trigger coverage
        self.driver.get("http://0.0.0.0:6543/?de")
        #self.driver.maximize_window()
        inputElement = self.driver.find_element_by_name("firstname")
        inputElement.send_keys("Christoph")
        self.driver.find_element_by_name('lastname').send_keys('Scheid')
        time.sleep(0.1)
        self.driver.find_element_by_name('email').send_keys('c@c3s.cc')
        time.sleep(0.1)
        self.driver.find_element_by_name('password').send_keys('foobar')
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
        self.driver.find_element_by_name('deformField14').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('other_colsoc').click()  # Yes
        #self.driver.find_element_by_id('other_colsoc-1').click()  # No
        time.sleep(0.1)
        self.driver.find_element_by_id(
            'colsoc_name').send_keys('GEMA')
        time.sleep(0.1)
        self.driver.find_element_by_name('got_statute').click()
        time.sleep(0.1)
        self.driver.find_element_by_name('num_shares').send_keys('7')

        self.driver.find_element_by_name('submit').click()

        self.failUnless('Email anfordern' in self.driver.page_source)

        # TODO: check contents of success page XXX
        self.assertTrue('Christoph' in self.driver.page_source)
        self.assertTrue('Scheid' in self.driver.page_source)
        self.assertTrue('Was nun passieren muss: Kontrolliere die Angaben '
                        'unten,' in self.driver.page_source)

        # TODO: check case colsoc = no views.py 765-767

        # TODO: check save to DB/randomstring: views.py 784-865

        # TODO: check re-edit of form: views.py 877-880 XXX
        #self.failUnless('Angaben ändern' in self.driver.page_source)
        self.driver.find_element_by_name('edit').click()
        # back to the form
        time.sleep(0.1)  # wait a little
        self.assertEqual(self.driver.find_element_by_name(
            'lastname').get_attribute('value'), 'Scheid')
        self.assertEqual(self.driver.find_element_by_name(
            'firstname').get_attribute('value'), 'Christoph')
        self.assertEqual(self.driver.find_element_by_name(
            'email').get_attribute('value'), 'c@c3s.cc')
        self.assertEqual(self.driver.find_element_by_name(
            'password').get_attribute('value'), 'foobar')
        self.assertEqual(self.driver.find_element_by_name(
            'address1').get_attribute('value'), 'addr one')
        self.assertEqual(self.driver.find_element_by_name(
            'address2').get_attribute('value'), 'addr two')
        self.assertEqual(self.driver.find_element_by_name(
            'postcode').get_attribute('value'), '98765')
        self.assertEqual(self.driver.find_element_by_name(
            'city').get_attribute('value'), 'townish')
        self.assertEqual(self.driver.find_element_by_name(
            'country').get_attribute('value'), 'GB')
        self.assertEqual(self.driver.find_element_by_name(
            'year').get_attribute('value'), '1998')
        self.assertEqual(self.driver.find_element_by_name(
            'month').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'day').get_attribute('value'), '12')
        self.assertEqual(self.driver.find_element_by_name(
            'deformField14').get_attribute('value'), 'normal')
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
        self.driver.find_element_by_id('other_colsoc-1').click()  # No colsoc
        self.driver.find_element_by_name('submit').click()
        time.sleep(0.1)
        self.assertTrue(
            'Bitte beachten: Es gab fehler' not in self.driver.page_source)
        self.assertTrue('addr two plus' in self.driver.page_source)

        self.driver.find_element_by_name('send_email').click()
        time.sleep(0.1)
        #import pdb
        #pdb.set_trace()

        page = self.driver.page_source
        self.assertTrue('C3S Mitgliedsantrag: Bitte Emails abrufen.' in page)
        self.assertTrue('Eine Email wurde verschickt,' in page)
        self.assertTrue('Christoph Scheid!' in page)

        self.assertTrue(
            u'Du wirst eine Email von noreply@c3s.cc mit einem ' in page)
        self.assertTrue(
            u'Bestätigungslink erhalten. Bitte rufe Deine Emails ab.' in page)

        self.assertTrue(u'Der Betreff der Email lautet:' in page)
        self.assertTrue(u'C3S: Email-Adresse' in page)
        #self.assertTrue(u'tigen und Formular abrufen.' in page)


class EmailVerificationTests(SeleniumTestBase):

    def setUp(self):
        super(EmailVerificationTests, self).setUp()

    def tearDown(self):
        self.driver.quit()
        call(['env/bin/pserve', 'development.ini', 'stop'])

    def test_verify_email(self):  # views.py 296-298
        url = "http://0.0.0.0:6543/verify/foo@shri.de/ABCDEFGHIJ"
        self.driver.get(url)

        self.assertTrue(
            'Bitte das Passwort eingeben.' in self.driver.page_source)
        self.assertTrue(
            'Hier geht es zum PDF...' in self.driver.page_source)
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
        self.driver.find_element_by_name('password').send_keys('berries')
        self.driver.find_element_by_name('submit').click()

        self.assertTrue('Lade dein PDF...' in self.driver.page_source)
        self.assertTrue(
            'C3S_SCE_AFM_Firstn_meLastname.pdf' in self.driver.page_source)

#        import pdb
#        pdb.set_trace()


#    def test_verify_email_wrong_pass(self):  # views.py 296-298
#        pass

#    def test_foo(self):
#        pass

class DashboardPageObject(object):
    def __init__(self):
        pass
        #ToDo: write page object


class OrderByTests(SeleniumTestBase):
    def setUp(self):
        super(OrderByTests, self).setUp()
        self.driver.get('')

    def tearDown(self):
        self.driver.quit()

    def test(self):
        url = "http://0.0.0.0:6543/dashboard/0/id/asc"
