#!/bin/env/python
# -*- coding: utf-8 -*-
"""
Tests for c3smembership.edit_member
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
from datetime import date, timedelta
from c3smembership import main
from webtest import TestApp
import webtest

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
        DBSession.close()
        DBSession.remove()
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        # self._insert_members()

        with transaction.manager:
                # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            DBSession.add(accountants_group)
            DBSession.flush()
            # staff personnel
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            DBSession.add(accountants_group)
            DBSession.add(staffer1)
            DBSession.flush()

        app = main({}, **my_settings)
        self.testapp = TestApp(app)

    def tearDown(self):
        """
        Tear down all test cases
        """
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    @staticmethod
    def __create_membership_applicant():
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

    @staticmethod
    def __create_accepted_member_full():
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

        member = EditMemberTests.__create_membership_applicant()
        DBSession.add(member)
        DBSession.flush()
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
                'email': u'info@c3s.cc',
                'address1': u'adressteil 1',
                'address2': u'adressteil 2',
                'postcode': u'12346',
                'city': u'die city',
                'country': u'FI',
                'membership_type': u'investing',
                'entity_type': u'legalentity',
                'other_colsoc': u'no',
                'name_of_colsoc': u'',
                'date_of_birth': '1999-12-30',
                'membership_date': '2013-09-24',
                'signature_received_date': '2013-09-24',
                'payment_received_date': '2013-09-24',
            },
            [
                u'EinNachname',
                u'info@c3s.cc',
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
        self.assertTrue('<h1>Details for' in res.body)

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

    @staticmethod
    def __validate_submit_error(res):
        """
        Submit the resource, validate that it was not successful and return
        the resulting resource
        """
        return res.form.submit('submit', status=200)

    @staticmethod
    def __set_form_properties(
            res,
            properties):
        """
        Set the properties of the form in the resource.
        """
        for key, value in properties.iteritems():
            res.form[key] = value

    def __validate_successful_edit(
            self,
            member_id,
            properties=None,
            body_content_parts=None):
        """
        Edit the member's properties, validate that it was successful,
        validate the body of the resulting resource and return it.
        """
        res = self.__get_edit_member(member_id)
        EditMemberTests.__set_form_properties(res, properties)
        res = self.__validate_successful_submit(res)
        self.__validate_body_content(res, body_content_parts)
        return res

    def __validate_abortive_edit(
            self,
            member_id,
            properties=None,
            body_content_parts=None):
        """
        Edit the member's properties, validate that it was not successful,
        validate the body of the resulting resource and return it.
        """
        res = self.__get_edit_member(member_id)
        EditMemberTests.__set_form_properties(res, properties)
        res = EditMemberTests.__validate_submit_error(res)
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
        self.failUnless('Membership Acquisition' in res.body)

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
        member = EditMemberTests.__create_membership_applicant()
        DBSession.add(member)
        DBSession.flush()

        # 1 Editing non members
        res = self.__get_edit_member(member.id)
        self.assertFalse(res.form['membership_accepted'].checked)

        # 1.1 Loss inputs must be hidden
        res = self.__get_edit_member(member.id)
        self.assertTrue(
            type(res.form['membership_loss_date']) == webtest.forms.Hidden)
        self.assertTrue(res.form['membership_loss_date'].value == '')
        self.assertTrue(
            type(res.form['membership_loss_type']) == webtest.forms.Hidden)
        self.assertTrue(res.form['membership_loss_type'].value == '')

        # 1.2 Hidden loss inputs should not make any problem and therefore
        #     submit without changes should work
        res = self.__get_edit_member(member.id)
        self.__validate_successful_submit(res)

        # 1.3 Try setting hidden values -> error
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_date': date.today(),
                'membership_loss_type': u'resignation',
            },
            [u'Please note: There were errors, please check the form below.'])

        # 2 Editing members
        member = EditMemberTests.__create_accepted_member_full()
        DBSession.add(member)
        DBSession.flush()
        res = self.__get_edit_member(member.id)
        # make sure default values are valid
        self.__validate_successful_submit(res)

        # 2.1 Loss inputs must not be hidden
        res = self.__get_edit_member(member.id)
        self.assertTrue(res.form['membership_accepted'].checked)
        self.assertTrue(
            type(res.form['membership_loss_date']) == webtest.forms.Text)
        self.assertTrue(res.form['membership_loss_date'].value == '')
        self.assertTrue(
            type(res.form['membership_loss_type']) == webtest.forms.Select)
        self.assertTrue(res.form['membership_loss_type'].value == '')

        # 2.2.1 Set only loss date -> error, set both
        self.__validate_abortive_edit(
            member.id,
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
                'membership_loss_date': '',
            })

        # 2.2.4 Set loss date and type to valid values -> success
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_type': 'resignation',
                'membership_loss_date': date(2016, 12, 31),
            })

        # 2.3 Loss date must be larger than acceptance date

        # 2.3.1 Set loss date prior to membership acceptance date -> error,
        #       set date larger membership acceptance
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_date': (
                    member.membership_date - timedelta(days=1)),
                'membership_loss_type': 'resignation',
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
                'membership_loss_date': date(2016, 12, 31),
                'membership_loss_type': 'resignation',
            })

        # 2.4 Loss date for resignation must be 31st of December

        # 2.4.1 Set loss type to resignation and loss date other than 31st
        #       of December -> fail
        self.__validate_abortive_edit(
            member.id,
            {
                'membership_loss_date': date(2016, 5, 28),
                'membership_loss_type': 'resignation',
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
                'membership_loss_date': date(2016, 10, 31),
                'membership_loss_type': 'resignation',
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
                'membership_loss_date': date(2016, 12, 30),
                'membership_loss_type': 'resignation',
            },
            [u'Resignations are only allowed to the 31st of December of a '
             'year.'])

        # 2.4.4 Set loss type to resignation and loss date to 31st of
        #       December succeed
        self.__validate_successful_edit(
            member.id,
            {
                'membership_loss_date': date(2016, 12, 31),
                'membership_loss_type': 'resignation',
            })

        # 2.5 Only natural persons can be set to loss type death

        # 2.5.1 Set loss type to death and entity type to legal entity ->
        #       error
        self.__validate_abortive_edit(
            member.id,
            {
                'entity_type': 'legalentity',
                'membership_loss_date': date(2016, 3, 25),
                'membership_loss_type': 'death',
            },
            [u'The membership loss type \'death\' is only allowed for natural '
             u'person members and not for legal entity members.'])

        # 2.5.2 Set loss type to death and entity type to natural person ->
        #       success
        self.__validate_successful_edit(
            member.id,
            {
                'entity_type': 'person',
                'membership_loss_date': date(2016, 3, 25),
                'membership_loss_type': 'death',
            })

        # 2.6 Only legal entites can be set to loss type winding-up

        # 2.6.1 Set loss type to winding-up and entity type to natural
        #       person error
        self.__validate_abortive_edit(
            member.id,
            {
                'entity_type': 'person',
                'membership_loss_date': date(2016, 3, 25),
                'membership_loss_type': 'winding-up',
            },
            [u'The membership loss type \'winding-up\' is only allowed for '
             u'legal entity members and not for natural person members.'])

        # 2.6.2 Set loss type to winding-up and entity type to legal entity
        #       -> success
        self.__validate_successful_edit(
            member.id,
            {
                'entity_type': 'legalentity',
                'membership_loss_date': date(2016, 3, 25),
                'membership_loss_type': 'winding-up',
            })
