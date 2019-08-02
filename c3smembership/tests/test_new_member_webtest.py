# -*- coding: utf-8 -*-
"""
Test new member by using WebTest
"""

from datetime import date
import unittest

import transaction
from webtest import TestApp

from pyramid import testing
from sqlalchemy import engine_from_config

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
        DBSession().close()
        DBSession.remove()
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        db_session = DBSession()
        with transaction.manager:
            # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            db_session.add(accountants_group)
            db_session.flush()
            # staff personnel
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
            )
            staffer1.groups = [accountants_group]
            db_session.add(accountants_group)
            db_session.add(staffer1)
            db_session.flush()

        from c3smembership import main
        app = main({}, **my_settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession().close()
        DBSession.remove()
        testing.tearDown()

    def _login(self):
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        res.form['login'] = 'rut'
        res.form['password'] = 'berries'
        res.form.submit('submit', status=302)

    @classmethod
    def __get_field_id_dict(cls, form):
        """
        Get a field id dict from the form

        Fields are not easily accessible from the form by id. Therefore, create
        a dictionary which maps the id to its field. Using the dict increases
        performance in case many fields have to be found by id.

        Args:
            form: webtest.forms.Form. The form to be transformed into a field
                id dict.

        Returns:
            dict mapping the id to its field.
        """
        field_id_dict = {}
        for key in form.fields.keys():
            fields = form.fields[key]
            for field in fields:
                field_id_dict[field.id] = field
        return field_id_dict

    def _fill_form_valid_natural(self, form):
        field_id_dict = self.__get_field_id_dict(form)
        form['firstname'] = u'SomeFirstname'
        form['lastname'] = u'SomeLastname'
        form['email'] = u'some@shri.de'
        form['address1'] = u"addr one"
        form['address2'] = u"addr two"
        form['postcode'] = u"12345"
        form['city'] = u"Footown Meeh"
        form['country'].value__set(u"DE")
        form['locale'] = u"DE"
        field_id_dict['date_of_birth'].value = \
            unicode(date(date.today().year-40, 1, 1))
        form['entity_type'].value__set(u'person')
        form['membership_type'].value__set(u'normal')
        form['other_colsoc'].value__set(u'no')
        form['name_of_colsoc'] = u"GEMA"
        form['num_shares'] = u'23'
        return form

    def _fill_form_valid_legal(self, form):
        field_id_dict = self.__get_field_id_dict(form)
        form['firstname'] = u'SomeLegalentity'
        form['lastname'] = u'SomeLegalName'
        form['email'] = u'legal@example.de'
        form['address1'] = u"addr one"
        form['address2'] = u"addr two"
        form['postcode'] = u"12345"
        form['city'] = u"Footown Meeh"
        form['country'].value__set(u"DE")
        form['locale'] = u"DE"
        field_id_dict['date_of_birth'].value = \
            unicode(date(date.today().year-40, 1, 1))
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
        self.assertTrue('Access was denied to this resource' in res.body)

        # so login first
        self._login()

        # no member with id=1 in DB
        res = self.testapp.get('/new_member?id=1', status=200)
        # enter valid data
        form = self._fill_form_valid_natural(res.form)
        res = form.submit(u'submit', status=302)
        res4 = res.follow()

        self.assertTrue('Membership application details' in res4.body)
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

        self.assertTrue('Membership application details' in res4.body)
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
