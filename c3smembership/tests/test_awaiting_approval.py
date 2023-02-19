# -*- coding: utf-8 -*-
"""
This module holds tests for the awaiting_approval module.
"""
from datetime import date
import unittest

from pyramid import testing
from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff

DEBUG = False


class AwaitingApprovalTests(unittest.TestCase):
    """
    test the "awaiting approval" view
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        self.session = DBSession()
        Base.metadata.create_all(engine)

        with transaction.manager:
            # a group for accountants/staff
            accountants_group = Group(name="staff")
            self.session.add(accountants_group)
            self.session.flush()

            # staff personnel
            staffer1 = Staff(
                login="rut",
                password="berries",
                email="noreply@example.com",
            )
            staffer1.groups = [accountants_group]
            self.session.add(accountants_group)
            self.session.add(staffer1)
            self.session.flush()

        from c3smembership import main
        app = main({}, **my_settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        self.session.close()
        DBSession.remove()
        testing.tearDown()

    def make_member_ready_for_approval(self):
        with transaction.manager:
            member1 = C3sMember(  # german
                firstname='SomeFirstnäme',
                lastname='SomeLastnäme',
                email='some@shri.de',
                address1="addr one",
                address2="addr two",
                postcode="12345",
                city="Footown Mäh",
                country="Foocountry",
                locale="DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGFOO',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc="GEMA",
                num_shares='23',
            )
            member1.signature_received = True
            member1.payment_received = True
        DBSession.add(member1)

    def test_awaiting_approval(self):
        '''
        tests for the awaiting approval view
        '''
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/afms_awaiting_approval', status=403)
        assert 'Access was denied to this resource' in res
        res = self.testapp.get('/login', status=200)
        self.assertTrue('login' in res)
        # try valid user
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # # being logged in ...
        res3 = res2.follow()  # being redirected to dashboard with parameters
        self.assertTrue('Acquisition of membership' in res3)
        # now look at the view to test
        res = self.testapp.get('/afms_awaiting_approval', status=200)
        self.assertTrue('Neue Genossenschaftsmitglieder' not in res)

        # create a member
        self.make_member_ready_for_approval()

        res = self.testapp.get('/afms_awaiting_approval', status=200)
        self.assertTrue('Neue Genossenschaftsmitglieder' in res)
        self.assertTrue('SomeFirstnäme' in res)
