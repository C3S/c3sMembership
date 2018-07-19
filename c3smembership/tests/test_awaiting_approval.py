# -*- coding: utf-8 -*-
"""
This module holds tests for the awaiting_approval module.
"""
import unittest
from pyramid import testing

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.models import (
    C3sMember,
    C3sStaff,
    Group,
)
from sqlalchemy import engine_from_config
import transaction
from datetime import date

DEBUG = False


class AwaitingApprovalTests(unittest.TestCase):
    """
    test the "awaiting approval" view
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
            # print "closed and removed DBSession"
        except:
            pass
            # print "no session to close"
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        with transaction.manager:
            # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                # print("adding group staff")
            except:
                # print("could not add group staff.")
                pass
            # staff personnel
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            try:
                DBSession.add(accountants_group)
                DBSession.add(staffer1)
                DBSession.flush()
            except:
                # print("it borked! (rut)")
                pass

        from c3smembership import main
        app = main({}, **my_settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    def make_member_ready_for_approval(self):
        with transaction.manager:
            member1 = C3sMember(  # german
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
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
        assert('Access was denied to this resource' in res.body)
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # # being logged in ...
        res3 = res2.follow()  # being redirected to dashboard with parameters
        self.failUnless(
            'Acquisition of membership' in res3.body)
        # now look at the view to test
        res = self.testapp.get('/afms_awaiting_approval', status=200)
        self.assertTrue('Neue Genossenschaftsmitglieder' not in res.body)

        # create a member
        self.make_member_ready_for_approval()

        res = self.testapp.get('/afms_awaiting_approval', status=200)
        self.assertTrue('Neue Genossenschaftsmitglieder' in res.body)
        self.assertTrue('SomeFirstnäme' in res.body)
