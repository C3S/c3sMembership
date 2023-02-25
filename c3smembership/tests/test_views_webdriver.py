import os
import subprocess
import socket
import glob
import datetime
import time
import inspect
import pytest

from sqlalchemy import engine_from_config
from paste.deploy.loadwsgi import appconfig
from webtest.http import StopableWSGIServer
from selenium.webdriver import Remote, Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)

# --- Config ------------------------------------------------------------------

CONFIG = {
    'host': '0.0.0.0',
    'port': 6544,
    'db': 'webdrivertest.db',
    'ini': "webdrivertest.ini",
    'screenshot_path': 'screenshots',
}


# --- Server ------------------------------------------------------------------

@pytest.fixture(autouse=True, scope='module')
def create_db_template():
    """
    Recreates the database template each run.
    """
    # remove db
    template_name = f"{CONFIG['db']}.template"
    if os.path.isfile(template_name):
        subprocess.run(('rm', template_name))
    # create db
    subprocess.run(('initialize_c3sMembership_db', CONFIG['ini']))
    # move db
    subprocess.run(('mv', CONFIG['db'], f"{CONFIG['db']}.template"))


@pytest.fixture(scope='class')
def copy_db_template():
    """
    Copies the database template for each test class to run on.
    """
    subprocess.run(('cp', f"{CONFIG['db']}.template", CONFIG['db']))


@pytest.fixture(autouse=True, scope='class')
def server(copy_db_template):
    """
    Provides the test server for each test class.
    """
    # start server
    config_path = 'config:' + os.path.join(
        os.path.dirname(__file__), '..', '..', CONFIG['ini'])
    config = appconfig(config_path)
    engine = engine_from_config(
        config, connect_args={"check_same_thread": False})
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    server = StopableWSGIServer.create(
        main({}, **config),
        host=CONFIG['host'],
        port=CONFIG['port'],
        clear_untrusted_proxy_headers=True
    )
    if not server.wait():
        raise Exception('Server could not be fired up. Exiting ...')
    # provide server
    try:
        yield server
    # stop server
    finally:
        server.shutdown()
        tries = 10
        while tries:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind((CONFIG['host'], CONFIG['port']))
                tries = 0
            except socket.error:
                tries -= 1
                time.sleep(0.5)
            finally:
                sock.close()


# --- Browser -----------------------------------------------------------------

@pytest.fixture(autouse=True, scope='module')
def browser():
    """
    Provides the test browser.
    """
    # start browser
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--verbose')
    grid_url = os.environ.get("SELENIUM_GRID_URL", False)
    if grid_url:
        browser = Remote(command_executor=grid_url, options=options)
    else:
        browser = Chrome(options=options)
    # provide browser
    try:
        yield browser
    # stop browser
    finally:
        browser.close()
        browser.quit()


@pytest.fixture(autouse=True)
def reset_browser_session(browser):
    browser.set_window_size(800, 600)
    browser.delete_all_cookies()


@pytest.fixture(autouse=True, scope="module")
def delete_screenshots():
    """
    Deletes all screenshots of previous selenium tests.
    """
    if not int(os.environ.get("SELENIUM_SCREENSHOTS", 0)):
        return
    path = os.path.join(CONFIG['screenshot_path'], '*.png')
    for screenshot in glob.glob(path):
        os.unlink(screenshot)


@pytest.fixture
def screenshot(browser):
    """
    Takes a screenshot of the current browser client viewport.
    """
    def do_screenshot(name=''):
        # create path
        path = CONFIG['screenshot_path']
        if not os.path.isdir(path):
            os.makedirs(path)
        # generate filename
        testtime = datetime.datetime.utcnow().strftime('%y%m%d.%H%M%S.%f')[:-4]
        testclass = ''
        testmethod = ''
        for frameinfo in inspect.stack():
            if frameinfo[3].startswith('test_'):
                testclass = frameinfo[0].f_locals["self"].__class__.__name__
                testmethod = frameinfo[3]
        filename = f"{testtime}-{testclass}.{testmethod}-{name}".strip("._-")
        # resize window
        size = browser.get_window_size()
        required_width = browser.execute_script(
            'return document.body.parentNode.scrollWidth')
        required_height = browser.execute_script(
            'return document.body.parentNode.scrollHeight')
        browser.set_window_size(required_width, required_height)
        # make screenshot
        browser.get_screenshot_as_file(os.path.join(path, filename + '.png'))
        # reset window size
        browser.set_window_size(size['width'], size['height'])
    yield do_screenshot


@pytest.fixture(autouse=True, scope='module')
def url():
    url = f"http://{os.environ.get('HOSTNAME', CONFIG['host'])}:{CONFIG['port']}"
    yield url


# --- Tests -------------------------------------------------------------------

class TestJoinForm:
    """
    Test the join form with selenium/webdriver.
    """
    def test_form_submission_de(self, browser, url, screenshot):
        """
        A webdriver test for the join form, German version
        """
        assert browser.get_cookies() == []

        # load the page with the form, choose german
        browser.get(f"{url}?de")
        source = browser.page_source
        screenshot('page-loaded')

        assert 'Mitgliedschaftsantrag' in source

        # check for cookie -- should be 'de' for germen
        assert browser.get_cookie('_LOCALE_')['value'] == 'de'

        # fill out the form
        browser.find_element(By.NAME, 'firstname').send_keys('Christoph')
        browser.find_element(By.NAME, 'lastname').send_keys('Scheid')
        browser.find_element(By.NAME, 'email').send_keys('c@example.com')
        browser.find_element(By.NAME, 'password').send_keys('foobar')
        browser.find_element(By.NAME, 'password-confirm').send_keys('foobar')
        browser.find_element(By.NAME, 'address1').send_keys('addr one')
        browser.find_element(By.NAME, 'address2').send_keys('addr two')
        browser.find_element(By.NAME, 'postcode').send_keys('98765')
        browser.find_element(By.NAME, 'city').send_keys('townish')
        browser.find_element(By.NAME, 'country').send_keys('Gri')
        browser.find_element(By.NAME, 'year').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'year').send_keys('1998')
        browser.find_element(By.NAME, 'month').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'month').send_keys('12')
        browser.find_element(By.NAME, 'day').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'day').send_keys('12')
        browser.find_element(By.NAME, 'membership_type').click()
        browser.find_element(By.NAME, 'other_colsoc').click()  # Yes
        browser.find_element(By.ID, 'colsoc_name').send_keys('GEMA')
        browser.find_element(By.NAME, 'got_statute').click()
        browser.find_element(By.NAME, 'got_dues_regulations').click()
        browser.find_element(By.NAME, 'privacy_consent').click()
        browser.find_element(By.NAME, 'num_shares').send_keys('7')

        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Nach Anfordern der Bestätigungsmail' in source

        # TODO: check contents of success page XXX
        assert 'Christoph' in source
        assert 'Scheid' in source
        assert 'Was nun passieren muss: Kontrolliere die Angaben' in source
        # TODO: check case colsoc = no views.py 765-767
        # TODO: check save to DB/randomstring: views.py 784-865

        # back to the form
        browser.find_element(By.ID, 'back').click()
        source = browser.page_source
        screenshot("form-back")

        assert browser.find_element(
               By.NAME, 'lastname').get_attribute('value') == 'Scheid'
        assert browser.find_element(
               By.NAME, 'firstname').get_attribute('value') == 'Christoph'
        assert browser.find_element(
               By.NAME, 'email').get_attribute('value') == 'c@example.com'
        assert browser.find_element(
               By.NAME, 'address1').get_attribute('value') == 'addr one'
        assert browser.find_element(
               By.NAME, 'address2').get_attribute('value') == 'addr two'
        assert browser.find_element(
               By.NAME, 'postcode').get_attribute('value') == '98765'
        assert browser.find_element(
               By.NAME, 'city').get_attribute('value') == 'townish'
        assert browser.find_element(
               By.NAME, 'country').get_attribute('value') == 'GR'
        assert browser.find_element(
               By.NAME, 'year').get_attribute('value') == '1998'
        assert browser.find_element(
               By.NAME, 'month').get_attribute('value') == '12'
        assert browser.find_element(
               By.NAME, 'day').get_attribute('value') == '12'
        assert browser.find_element(
               By.NAME, 'membership_type').get_attribute('value') == 'normal'
        assert browser.find_element(
               By.NAME, 'other_colsoc').get_attribute('value') == 'yes'
        assert browser.find_element(
               By.ID, 'colsoc_name').get_attribute('value') == 'GEMA'
        assert browser.find_element(
               By.NAME, 'num_shares').get_attribute('value') == '17'

        # change a detail
        browser.find_element(By.NAME, 'address2').send_keys(' plus')
        # ok, all data checked, submit again
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Bitte beachten: Es gab Fehler. Bitte Eingaben unten' in source

        # verify we have to check this again
        browser.find_element(By.NAME, 'got_statute').click()
        browser.find_element(By.NAME, 'got_dues_regulations').click()
        browser.find_element(By.NAME, 'privacy_consent').click()
        browser.find_element(By.ID, 'other_colsoc-1').click()
        browser.find_element(By.ID, 'colsoc_name').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.ID, 'colsoc_name').send_keys(Keys.DELETE)
        # enter password
        browser.find_element(By.NAME, 'password').send_keys('foobar')
        browser.find_element(By.NAME, 'password-confirm').send_keys('foobar')

        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Bitte beachten: Es gab fehler' not in source
        assert 'addr two plus' in source

        browser.find_element(By.ID, 'next').click()
        source = browser.page_source
        screenshot("form-next")

        assert 'C3S Mitgliedsantrag: Bitte E-Mails abrufen.' in source
        assert 'Eine E-Mail wurde verschickt,' in source
        assert 'Christoph Scheid!' in source
        assert 'Du wirst eine E-Mail' in source
        assert 'Bestätigungslink' in source
        assert 'Der Betreff der E-Mail lautet:' in source
        assert 'C3S: E-Mail-Adresse' in source
        assert 'tigen und Formular abrufen' in source

    def test_form_submission_en(self, browser, url, screenshot):
        """
        A webdriver test for the join form, english version
        """
        assert browser.get_cookies() == []

        # load the page with the form, choose german
        browser.get(f"{url}?en")
        source = browser.page_source
        screenshot('page-loaded')

        assert 'Application for Membership' in source

        # check for cookie -- should be 'en' for english
        assert browser.get_cookie('_LOCALE_')['value'] == 'en'

        # fill out the form
        browser.find_element(By.NAME, 'firstname').send_keys('Christoph')
        browser.find_element(By.NAME, 'lastname').send_keys('Scheid')
        browser.find_element(By.NAME, 'email').send_keys('c@example.com')
        browser.find_element(By.NAME, 'password').send_keys('foobar')
        browser.find_element(By.NAME, 'password-confirm').send_keys('foobar')
        browser.find_element(By.NAME, 'address1').send_keys('addr one')
        browser.find_element(By.NAME, 'address2').send_keys('addr two')
        browser.find_element(By.NAME, 'postcode').send_keys('98765')
        browser.find_element(By.NAME, 'city').send_keys('townish')
        browser.find_element(By.NAME, 'country').send_keys('Gri')
        browser.find_element(By.NAME, 'year').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'year').send_keys('1998')
        browser.find_element(By.NAME, 'month').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'month').send_keys('12')
        browser.find_element(By.NAME, 'day').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.NAME, 'day').send_keys('12')
        browser.find_element(By.NAME, 'membership_type').click()
        browser.find_element(By.NAME, 'other_colsoc').click()  # Yes
        browser.find_element(By.ID, 'colsoc_name').send_keys('GEMA')
        browser.find_element(By.NAME, 'got_statute').click()
        browser.find_element(By.NAME, 'got_dues_regulations').click()
        browser.find_element(By.NAME, 'privacy_consent').click()
        browser.find_element(By.NAME, 'num_shares').send_keys('7')

        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Click the button to have an email' in source

        # TODO: check contents of success page XXX
        assert 'Christoph' in source
        assert 'Scheid' in source
        assert 'What happens next: You need to check the information' in source
        # TODO: check case colsoc = no views.py 765-767
        # TODO: check save to DB/randomstring: views.py 784-865
        # TODO: check re-edit of form: views.py 877-880 XXX

        # back to the form
        browser.find_element(By.ID, 'back').click()
        source = browser.page_source
        screenshot("form-back")

        assert browser.find_element(
               By.NAME, 'lastname').get_attribute('value') == 'Scheid'
        assert browser.find_element(
               By.NAME, 'firstname').get_attribute('value') == 'Christoph'
        assert browser.find_element(
               By.NAME, 'email').get_attribute('value') == 'c@example.com'
        assert browser.find_element(
               By.NAME, 'address1').get_attribute('value') == 'addr one'
        assert browser.find_element(
               By.NAME, 'address2').get_attribute('value') == 'addr two'
        assert browser.find_element(
               By.NAME, 'postcode').get_attribute('value') == '98765'
        assert browser.find_element(
               By.NAME, 'city').get_attribute('value') == 'townish'
        assert browser.find_element(
               By.NAME, 'country').get_attribute('value') == 'GR'
        assert browser.find_element(
               By.NAME, 'year').get_attribute('value') == '1998'
        assert browser.find_element(
               By.NAME, 'month').get_attribute('value') == '12'
        assert browser.find_element(
               By.NAME, 'day').get_attribute('value') == '12'
        assert browser.find_element(
               By.NAME, 'membership_type').get_attribute('value') == 'normal'
        assert browser.find_element(
               By.NAME, 'other_colsoc').get_attribute('value') == 'yes'
        assert browser.find_element(
               By.ID, 'colsoc_name').get_attribute('value') == 'GEMA'
        assert browser.find_element(
               By.NAME, 'num_shares').get_attribute('value') == '17'

        # change a detail
        browser.find_element(By.NAME, 'address2').send_keys(' plus')
        # ok, all data checked, submit again
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Please note: There were errors, please check the' in source

        # verify we have to check this again
        browser.find_element(By.NAME, 'got_statute').click()
        browser.find_element(By.NAME, 'got_dues_regulations').click()
        browser.find_element(By.NAME, 'privacy_consent').click()
        browser.find_element(By.ID, 'other_colsoc-1').click()
        browser.find_element(By.ID, 'colsoc_name').send_keys(Keys.CONTROL, "a")
        browser.find_element(By.ID, 'colsoc_name').send_keys(Keys.DELETE)
        # enter password
        browser.find_element(By.NAME, 'password').send_keys('foobar')
        browser.find_element(By.NAME, 'password-confirm').send_keys('foobar')

        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Please note: There were errors, please check the' not in source
        assert 'addr two plus' in source

        browser.find_element(By.ID, 'next').click()
        source = browser.page_source
        screenshot("form-next")

        assert 'C3S Membership Application: Check your email' in source
        assert 'An email was sent,' in source
        assert 'Christoph Scheid!' in source
        assert 'You will receive an email from us with' in source
        assert 'The email subject line will read:' in source
        assert 'C3S: confirm your email address ' in source
        assert 'and load your PDF' in source


class TestEmailVerification:
    """
    Tests for the view where users are sent after submitting their data.
    They must enter their password and thereby confirm their email address,
    as they got to this form by clicking on a link supplied by mail.
    """

    def test_verify_email_de(self, browser, url, screenshot):
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        browser.get(f"{url}/verify/uat.yes@example.com/ABCDEFGHIJ?de")
        source = browser.page_source
        screenshot("page-loaded")

        assert 'Bitte gib Dein Passwort ein, um' in source
        assert 'Deine E-Mail-Adresse zu bestätigen.' in source
        assert 'Hier geht es zum PDF...' in source

        # try with empty or wrong password -- must fail
        browser.find_element(By.NAME, 'password').send_keys('')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Bitte das Passwort eingeben.' in source
        assert 'Hier geht es zum PDF...' in source

        # wrong password
        browser.find_element(By.NAME, 'password').send_keys('schmoo')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Bitte das Passwort eingeben.' in source
        assert 'Hier geht es zum PDF...' in source

        # try correct password
        browser.find_element(By.NAME, 'password').send_keys('berries')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Lade Dein PDF...' in source
        assert 'C3S_SCE_AFM_Firstn_meLastname.pdf' in source
        # XXX TODO: check PDF download

    def test_verify_email_en(self, browser, url, screenshot):
        """
        This test checks -- after an application has been filled out --
        for the password supplied during application.
        If the password matches the email address, a link to a PDF is given.
        Thus, an half-ready application must be present in the DB.
        """
        browser.get(f"{url}/verify/uat.yes@example.com/ABCDEFGHIJ?en")
        source = browser.page_source
        screenshot("page-loaded")

        # check text on page
        assert 'Please enter your password in order ' in source
        assert 'to verify your email address.' in source

        # enter empty or wrong password -- must fail
        # empty password
        browser.find_element(By.NAME, 'password').send_keys('')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Please enter your password.' in source

        # wrong password
        browser.find_element(By.NAME, 'password').send_keys('schmoo')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Please enter your password.' in source

        # try correct password
        browser.find_element(By.NAME, 'password').send_keys('berries')
        screenshot("form-edited")
        browser.find_element(By.NAME, 'submit').click()
        source = browser.page_source
        screenshot("form-sent")

        assert 'Load your PDF' in source
        assert 'C3S_SCE_AFM_Firstn_meLastname.pdf' in source
        # XXX TODO: check PDF download
