#!/bin/env/python
# -*- coding: utf-8 -*-

from datetime import date

from pyramid import testing
from sqlalchemy import engine_from_config
import transaction
import unittest

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


class NewMemberTests(unittest.TestCase):
    """
    test creation of a new member by staff

    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
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
        # self.session = DBSession()
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
            except:
                pass
            # staff personnel
            staffer1 = Staff(
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

    def _login(self):
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        res.form['login'] = 'rut'
        res.form['password'] = 'berries'
        res.form.submit('submit', status=302)

    def _fill_form_valid_natural(self, form):
        # print form.fields
        form['firstname'] = u'SomeFirstname'
        form['lastname'] = u'SomeLastname'
        form['email'] = u'some@shri.de'
        form['address1'] = u"addr one"
        form['address2'] = u"addr two"
        form['postcode'] = u"12345"
        form['city'] = u"Footown Meeh"
        form['country'].value__set(u"DE")
        form['locale'] = u"DE"
        form['date_of_birth'] = unicode(date(date.today().year-40, 1, 1))
        form['entity_type'].value__set(u'person')
        form['membership_type'].value__set(u'normal')
        form['other_colsoc'].value__set(u'no')
        form['name_of_colsoc'] = u"GEMA"
        form['num_shares'] = u'23'
        return form

    def _fill_form_valid_legal(self, form):
        form['firstname'] = u'SomeLegalentity'
        form['lastname'] = u'SomeLegalName'
        form['email'] = u'legal@example.de'
        form['address1'] = u"addr one"
        form['address2'] = u"addr two"
        form['postcode'] = u"12345"
        form['city'] = u"Footown Meeh"
        form['country'].value__set(u"DE")
        form['locale'] = u"DE"
        form['date_of_birth'] = unicode(date(date.today().year-40, 1, 1))
        form['entity_type'] = u'legalentity'
        form['membership_type'] = u'investing'
        form['other_colsoc'].value__set(u'no')
        form['name_of_colsoc'] = u""
        form['num_shares'] = u'42'
        return form


    def test_add_member(self):
        '''
        tests for the new_member view
        '''
        # unauthorized access must be prevented
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/new_member', status=403)
        assert('Access was denied to this resource' in res.body)

        # so login first
        self._login()

        # no member with id=1 in DB
        res = self.testapp.get('/new_member?id=1', status=200)
        # enter valid data
        form = self._fill_form_valid_natural(res.form)
        res = form.submit(u'submit', status=302)
        res4 = res.follow()

        self.assertTrue('Details for Member Application #1' in res4.body)
        self.assertTrue('SomeFirstname' in res4.body)
        self.assertTrue('SomeLastname' in res4.body)
        self.assertTrue('some@shri.de' in res4.body)
        self.assertTrue('addr one' in res4.body)
        self.assertTrue('addr two' in res4.body)
        self.assertTrue('12345' in res4.body)
        self.assertTrue('DE' in res4.body)
        self.assertTrue('normal' in res4.body)
        self.assertTrue('23' in res4.body)

        # now, there is a member with id=1 in DB
        res = self.testapp.get('/new_member?id=1', status=200)

        # check the number of entries in the DB
        self.assertEqual(C3sMember.get_number(), 1)


        res = self.testapp.get('/new_member', status=200)
        form = self._fill_form_valid_legal(res.form)
        res = form.submit(u'submit', status=302)
        res4 = res.follow()

        self.assertTrue('Details for Member Application #2' in res4.body)
        self.assertTrue('SomeLegalentity' in res4.body)
        self.assertTrue('SomeLegalName' in res4.body)
        self.assertTrue('legal@example.de' in res4.body)
        self.assertTrue('addr one' in res4.body)
        self.assertTrue('addr two' in res4.body)
        self.assertTrue('12345' in res4.body)
        self.assertTrue('' in res4.body)
        self.assertTrue('DE' in res4.body)
        self.assertTrue('investing' in res4.body)
        self.assertTrue('42' in res4.body)
