# -*- coding: utf-8 -*-
"""
Base for integration tests
"""

import re
from unittest import TestCase

from sqlalchemy import engine_from_config
import transaction
from webtest import (
    AppError,
    TestApp,
)

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


class IntegrationTestCaseBase(TestCase):
    """
    TestCase base class for integration tests

    The TestApp is only created once and reset for each derived testcase to
    save resources.
    """

    APP = None
    TESTAPP = None
    FLASH_REGEX = re.compile(
        r'<div\s*role="alert"\s*class="alert alert-(?P<queue>[^<]*)">\s*'
        r'(?P<message>.*)\s*</div>')
    SETTINGS = {
        'sqlalchemy.url': 'sqlite:///:memory:',
        'api_auth_token': u"SECRETAUTHTOKEN",
        'c3smembership.notification_sender': 'membership@example.com',
        'c3smembership.url': 'http://membership.example.com',
        'testing.mail_to_console': 'false',
        'available_languages': 'en de',
    }

    @classmethod
    def setUpClass(cls):
        """
        Setup app, web app and database

        The database is initialized with a staff login. App and web app are
        reused if already available. The database is reinitialized each time.
        """
        if IntegrationTestCaseBase.TESTAPP is None:
            # Initialize test app
            cls.__set_up_database()
            if IntegrationTestCaseBase.APP is None:
                IntegrationTestCaseBase.APP = main({}, **cls.SETTINGS)
                cls.app = IntegrationTestCaseBase.APP
            IntegrationTestCaseBase.TESTAPP = TestApp(
                IntegrationTestCaseBase.APP)
            cls.testapp = IntegrationTestCaseBase.TESTAPP
        else:
            # Reuse test app
            cls.testapp = IntegrationTestCaseBase.TESTAPP
            cls.app = IntegrationTestCaseBase.APP
            cls.testapp.reset()
            # Setup new database for new test case
            cls.__set_up_database()

    @classmethod
    def tearDownClass(cls):
        """
        Remove the database

        The database must be set up each time a test case is initialized in
        order to have clean data.
        """
        db_session = cls.get_db_session()
        db_session.close()
        DBSession.remove()

    @classmethod
    def __set_up_database(cls):
        """
        Set up the database and create staff
        """
        engine = engine_from_config(cls.SETTINGS)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        cls.__create_staff()

    @classmethod
    def __create_staff(cls):
        """
        Create a staff entry in the database
        """
        with transaction.manager:
            db_session = cls.get_db_session()
            accountants_group = Group(name=u"staff")
            db_session.add(accountants_group)
            staffer = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
            )
            staffer.groups = [accountants_group]
            db_session.add(accountants_group)
            db_session.add(staffer)
            db_session.flush()

    def log_in(self):
        """
        Log into the membership backend
        """
        # Try logging in
        response = self.testapp.get('/login')
        if response.status_code == 200:
            # Fill out login form
            self.failUnless('login' in response.body)
            form = response.form
            form['login'] = 'rut'
            form['password'] = 'berries'
            form.submit('submit', status=302)
        elif response.status_code == 302:
            # Verify already logged in
            self.assertTrue('dashboard' in response.location)
            response.follow(status=200)

    def log_out(self):
        """
        Log out of the membership backend
        """
        result = self.testapp.get('/logout', status=302)
        self.assertTrue('/login' in result.location)

    def assert_get_unauthorized(self, *args, **kwargs):
        """
        Assert that the GET request receives a 403 Forbidden response

        The parameters are passed to the ``webtest.TestApp.get`` method.
        """
        with self.assertRaises(AppError) as raise_context:
            self.testapp.get(*args, **kwargs)
        self.assertTrue('403 Forbidden' in raise_context.exception.message)

    @classmethod
    def get_db_session(cls):
        """
        Get an instance of the current database session
        """
        return DBSession()

    def assert_flash(self, response, queue, message, exact_message=False):
        """
        Assert that a flash message exists in the queue

        The response's body is checked for flash messages and it is verfied
        that the message exists in the queue.

        Args:
            response: The response which is checked for the flash message.
            queue: The name of the queue from which the message is checked.
            message: The message against which to check the queue.
            exact_message: Optional boolean, defaults to False. If True the
                message must be exactly equal, if False message must be a part
                of the flash message.
        """
        matches = re.findall(self.FLASH_REGEX, response.body)
        for match in matches:
            match_queue = match[0]
            match_message = match[1]
            if match_queue == queue:
                if exact_message:
                    if match_message == message:
                        return True
                else:
                    if message in match_message:
                        return True
        raise AssertionError(
            'Flash message "{message}" not found in quene "{queue}".'.format(
                message=message, queue=queue))

    def assert_get_redirect_flash(self, url, location, queue, message):
        """
        Assert the get redirects to the specified location and flashes a
        message to the queue

        Args:
            url: The GET URL
            location: The location against with the redirect is verified
            queue: The flash queue
            message: The message in the flash queue
        """
        response = self.testapp.get(url, status=302)
        self.assertTrue(location in response.location)
        response = response.follow()
        self.assert_flash(response, queue, message)
