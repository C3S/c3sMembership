#!/bin/env/python
# -*- coding: utf-8 -*-
"""
Tests for c3smembership.presentation.views.membership_member_edit
"""

from datetime import date, timedelta
import unittest

import transaction
import webtest
from webtest import TestApp

from pyramid import testing
from sqlalchemy import engine_from_config

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff

DEBUG = False


class EditMemberTests(unittest.TestCase):
    """
    these tests are functional tests to check functionality of the whole app
    (i.e. integration tests)
    they also serve to get coverage for 'main'
    """
    def setUp(self):
        """
        Setup test cases
        """
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

        # self._insert_members()
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

        app = main({}, **my_settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        """
        Tear down all test cases
        """
        DBSession().close()
        DBSession.remove()
        testing.tearDown()

    @classmethod
    def __create_membership_applicant(cls):
        """
        Create and return a membership applicant
        """
        member = None
        with transaction.manager:
            member = C3sMember(  # german
                firstname=u'SomeFirstnäme',
                lastname=u'Membership Applicant',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date(1970, 1, 1),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date(2015, 1, 1),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
        return member

    @classmethod
    def __create_accepted_member_full(cls):
        """
        Creates and returns an accepted full member
        """
        member = None
        with transaction.manager:
            member = C3sMember(  # german
                firstname=u'SomeFirstnäme',
                lastname=u'Accepted Full Member',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date(1970, 1, 1),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date(2014, 1, 1),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            member.membership_accepted = True
            member.membership_date = date(2015, 1, 1)
        return member

    def test_edit_members(self):
        '''
        tests for the edit_member view
        '''
        # unauthorized access must be prevented
        res = self.testapp.reset()  # delete cookie
        res = self.testapp.get('/edit/1', status=403)
        self.failUnless('Access was denied to this resource' in res.body)

        self.__login()

        # no member in DB, so redirecting to dashboard
        res = self.testapp.get('/edit/1', status=302)
        self.__validate_dashboard_redirect(res)

        member = self.__create_membership_applicant()
        DBSession().add(member)
        DBSession().flush()
        # now there is a member in the DB

        # let's try invalid input
        res = self.testapp.get('/edit/foo', status=302)
        self.__validate_dashboard_redirect(res)

        # now try valid id
        res = self.__get_edit_member(member.id)

        # set the date correctly
        self.__validate_successful_edit(
            member.id,
            {
                'firstname': u'EinVörname',
                'lastname': u'EinNachname',
                'email': u'info@example.com',
                'address1': u'adressteil 1',
                'address2': u'adressteil 2',
                'postcode': u'12346',
                'city': u'die city',
                'country': u'FI',
                'membership_type': u'investing',
                'entity_type': u'legalentity',
                'other_colsoc': u'no',
                'name_of_colsoc': u'',
            },
            {
                'date_of_birth': '1999-12-30',
                'membership_date': '2013-09-24',
                'signature_received_date': '2013-09-24',
                'payment_received_date': '2013-09-24',
            },
            [
                u'EinNachname',
                u'info@example.com',
                u'adressteil 1',
                u'adressteil 2',
                u'12346',
                u'die city',
                u'FI',
                u'investing',
            ])

        # edit again ... changing membership acceptance status
        self.__validate_successful_edit(
            member.id,
            {
                'membership_accepted': True,
            })

    def __validate_details_page(self, res):
        """
        Validate that the resource in res is the details page
        """
        self.assertTrue(
            'Member details' in res.body or
            'Membership application details' in res.body)

    def __validate_successful_submit(self, res):
        """
        Submit the resource, validate that it was successful and return the
        resulting resource.
        """
        res = res.form.submit('submit', status=302)
        res = res.follow()
        self.__validate_details_page(res)
        return res

    def __validate_body_content(self, res, body_content_parts):
        """
        Validate that the body_content_parts occur within the resource's body.
        """
        if body_content_parts is not None:
            for body_content_part in body_content_parts:
                self.assertTrue(body_content_part.decode(
                    'utf-8') in res.body.decode('utf-8'))

    @classmethod
    def __validate_submit_error(cls, res):
        """
        Submit the resource, validate that it was not successful and return
        the resulting resource
        """
        return res.form.submit('submit', status=200)

    @classmethod
    def __set_form_properties(
            cls,
            form,
            name_properties,
            id_properties=None):
        """
        Set the properties of the form in the resource.

        Args:
            form: webtest.forms.Form. The form in which to set the properties
            name_properties: dict. Properties to set by the field's name
            id_properties: dict. Properties to set by the field's id
        """
        if name_properties:
            for key, value in name_properties.iteritems():
                form[key] = value

        if id_properties:
            field_id_dict = cls.__get_field_id_dict(form)
            for key, value in id_properties.iteritems():
                field_id_dict[key].value = value

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

    def __validate_successful_edit(
            self,
            member_id,
            name_properties=None,
            id_properties=None,
            body_content_parts=None):
        """
        Edit the member's properties, validate that it was successful,
        validate the body of the resulting resource and return it.
        """
        res = self.__get_edit_member(member_id)
        self.__set_form_properties(res.form, name_properties, id_properties)
        res = self.__validate_successful_submit(res)
        self.__validate_body_content(res, body_content_parts)
        return res

    def __validate_abortive_edit(
            self,
            member_id,
            name_properties=None,
            id_properties=None,
            body_content_parts=None):
        """
        Edit the member's properties, validate that it was not successful,
        validate the body of the resulting resource and return it.
        """
        res = self.__get_edit_member(member_id)
        self.__set_form_properties(res.form, name_properties, id_properties)
        res = self.__validate_submit_error(res)
        self.__validate_body_content(res, body_content_parts)
        return res

    def __get_edit_member(self, member_id):
        """
        Get the edit page for the member and validate it's successful
        retrieval.
        """
        res = self.testapp.get(
            '/edit/{0}'.format(member_id),
            status=200)
        self.failUnless('Edit member' in res.body)
        return res

    def __login(self):
        """
        Log into the membership backend
        """
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res = form.submit('submit', status=302)
        res = res.follow()  # being redirected to dashboard_only
        self.__validate_dashboard(res)

    def __validate_dashboard_redirect(self, res):
        """
        Validate that res is redirecting to the dashboard
        """
        res = res.follow()  # being redirected to dashboard with parameters
        self.__validate_dashboard(res)

    def __validate_dashboard(self, res):
        """
        Validate that res is the dashboard
        """
        self.failUnless('Acquisition of membership' in res.body)

    @classmethod
    def __get_field_by_id(cls, form, field_id):
        """
        Get a field by its id

        Args:
            form: webtest.forms.Form. The form from which to get the field by
                its id
            field_id: String. The id of the field.

        Returns:
            webtest.forms.Field or subtype object of the specified id.
        """
        field_id_dict = cls.__get_field_id_dict(form)
        return field_id_dict[field_id]

    def test_membership_loss(self):
        '''
        Test the loss of membership.

        Test cases for:

        1 Editing non members

          1.1 Loss inputs must be hidden
          1.1 Hidden loss inputs should not make any problem and therefore
              submit without changes should work
          1.2 Try setting hidden values -> error

        2 Editing members

          2.1 Loss inputs must not be hidden

          2.2 Loss date and loss type must both be either set or unset

            2.2.1 Set only loss date -> error, set both
            2.2.2 Set only loss type -> error, set both
            2.2.3 Set neither loss date nor type -> success
            2.2.4 Set loss date and type to valid values -> success

          2.3 Loss date must be larger than acceptance date

            2.3.1 Set loss date prior to membership acceptance date -> error,
                  set date larger membership acceptance
            2.3.2 Set loss date after membership acceptance date -> success

          2.4 Loss date for resignation must be 31st of December

            2.4.1 Set loss type to resignation and loss date other than 31st
                  of December -> fail
            2.4.2 Set loss type to resignation and loss date to 31st but not
                  December -> fail
            2.4.3 Set loss type to resignation and loss date to December but
                  not 31st -> fail
            2.4.4 Set loss type to resignation and loss date to 31st of
                  December succeed

          2.5 Only natural persons can be set to loss type death

            2.5.1 Set loss type to death and entity type to legal entity ->
                  error
            2.5.2 Set loss type to death and entity type to natural person ->
                  success

          2.6 Only legal entites can be set to loss type winding-up

            2.6.1 Set loss type to winding-up and entity type to natural
                  person error
            2.6.2 Set loss type to winding-up and entity type to legal entity
                  -> success
        '''
        # setup
        res = self.testapp.reset()
        self.__login()
        member = self.__create_membership_applicant()
        db_session = DBSession()
        db_session.add(member)
        db_session.flush()

        # 1 Editing non members
        res = self.__get_edit_member(member.id)
        self.assertFalse(res.form['membership_accepted'].checked)

        # 1.1 Loss inputs must be hidden
        res = self.__get_edit_member(member.id)
        self.assertTrue(
            isinstance(res.form['membership_loss_date'], webtest.forms.Hidden))
        self.assertTrue(res.form['membership_loss_date'].value == '')
        self.assertTrue(
            isinstance(res.form['membership_loss_type'], webtest.forms.Hidden))
        self.assertTrue(res.form['membership_loss_type'].value == '')

        # 1.2 Hidden loss inputs should not make any problem and therefore
        #     submit without changes should work
        res = self.__get_edit_member(member.id)
        self.__validate_successful_submit(res)

        # 1.3 Try setting hidden values -> error
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': u'resignation',
            },
            {
                'membership_loss_date': date.today(),
            },
            [u'Please note: There were errors, please check the form below.'])

        # 2 Editing members
        member = self.__create_accepted_member_full()
        db_session.add(member)
        db_session.flush()
        res = self.__get_edit_member(member.id)
        # make sure default values are valid
        self.__validate_successful_submit(res)

        # 2.1 Loss inputs must not be hidden
        res = self.__get_edit_member(member.id)
        membership_loss_date_field = self.__get_field_by_id(
            res.form, 'membership_loss_date')
        self.assertTrue(res.form['membership_accepted'].checked)
        self.assertTrue(
            isinstance(membership_loss_date_field, webtest.forms.Field))
        self.assertTrue(
            membership_loss_date_field.value == '')
        self.assertTrue(
            isinstance(res.form['membership_loss_type'], webtest.forms.Select))
        self.assertTrue(res.form['membership_loss_type'].value == '')

        # 2.2.1 Set only loss date -> error, set both
        self.__validate_abortive_edit(
            member.id,
            {},
            {
                'membership_loss_date': date(2016, 12, 31),
            },
            [
                'Please note: There were errors, please check the form '
                'below.',
                'Date and type of membership loss must be set both or none.',
            ])

        # 2.2.2 Set only loss type -> error, set both
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {},
            [
                'Please note: There were errors, please check the form '
                'below.',
                'Date and type of membership loss must be set both or none.',
            ])

        # 2.2.3 Set neither loss date nor type -> success
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_type': '',
            },
            {
                'membership_loss_date': '',
            })

        # 2.2.4 Set loss date and type to valid values -> success
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 12, 31),
            })

        # 2.3 Loss date must be larger than acceptance date

        # 2.3.1 Set loss date prior to membership acceptance date -> error,
        #       set date larger membership acceptance
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': (
                    member.membership_date - timedelta(days=1)),
            },
            [
                'Please note: There were errors, please check the form '
                'below.',
                'Date membership loss must be larger than membership '
                'acceptance date.',
            ])

        # 2.3.2 Set loss date after membership acceptance date -> success
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 12, 31),
            })

        # 2.4 Loss date for resignation must be 31st of December

        # 2.4.1 Set loss type to resignation and loss date other than 31st
        #       of December -> fail
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 5, 28),
            },
            [
                'Please note: There were errors, please check the form '
                'below.',
                'Resignations are only allowed to the 31st of December of a '
                'year.',
            ])

        # 2.4.2 Set loss type to resignation and loss date to 31st but not
        #       December -> fail
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 10, 31),
            },
            [
                'Please note: There were errors, please check the form '
                'below.',
                'Resignations are only allowed to the 31st of December of a '
                'year.',
            ])

        # 2.4.3 Set loss type to resignation and loss date to December but
        #       not 31st -> fail
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 12, 30),
            },
            [u'Resignations are only allowed to the 31st of December of a '
             'year.'])

        # 2.4.4 Set loss type to resignation and loss date to 31st of
        #       December succeed
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
            },
            {
                'membership_loss_date': date(2016, 12, 31),
            })

        # 2.5 Only natural persons can be set to loss type death

        # 2.5.1 Set loss type to death and entity type to legal entity ->
        #       error
        self.__validate_abortive_edit(
            member.id,
            {
                'entity_type': 'legalentity',
                'membership_loss_type': 'death',
            },
            {
                'membership_loss_date': date(2016, 3, 25),
            },
            [u'The membership loss type \'death\' is only allowed for natural '
             u'person members and not for legal entity members.'])

        # 2.5.2 Set loss type to death and entity type to natural person ->
        #       success
        self.__validate_successful_edit(
            member.id,
            {
                'entity_type': 'person',
                'membership_loss_type': 'death',
            },
            {
                'membership_loss_date': date(2016, 3, 25),
            })

        # 2.6 Only legal entites can be set to loss type winding-up

        # 2.6.1 Set loss type to winding-up and entity type to natural
        #       person error
        self.__validate_abortive_edit(
            member.id,
            {
                'entity_type': 'person',
                'membership_loss_type': 'winding-up',
            },
            {
                'membership_loss_date': date(2016, 3, 25),
            },
            [u'The membership loss type \'winding-up\' is only allowed for '
             u'legal entity members and not for natural person members.'])

        # 2.6.2 Set loss type to winding-up and entity type to legal entity
        #       -> success
        self.__validate_successful_edit(
            member.id,
            {
                'entity_type': 'legalentity',
                'membership_loss_type': 'winding-up',
            },
            {
                'membership_loss_date': date(2016, 3, 25),
            })
