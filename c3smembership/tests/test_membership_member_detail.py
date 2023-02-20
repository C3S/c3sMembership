# -*- coding: utf-8 -*-
"""
Integration test the c3smembership.presentation.views.membership_member_detail
package
"""

from datetime import date

from unittest.mock import Mock

from .integration_test_base import IntegrationTestCaseBase

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.views import membership_member_detail


class MemberDetailIntegration(IntegrationTestCaseBase):
    """
    Integration testing of the membership_acquisition module
    """

    @classmethod
    def setUpClass(cls):
        super(MemberDetailIntegration, cls).setUpClass()
        db_session = cls.get_db_session()
        cls.member = C3sMember(
            firstname='SomeFirstnäme',
            lastname='SomeLastnäme',
            email='member@example.com',
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
            num_shares=23,
        )
        cls.member.membership_number = 1
        cls.member.membership_accepted = True
        db_session.add(cls.member)
        db_session.flush()

    def test_member_details(self):
        """
        Test the member_details view

        1. Get member details

           1. At least contain name and address
           2. Access is logged

        2. Verification fails if not a number
        3. Verification fails if membership number not found
        4. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Get member details
        logger_mock = Mock()
        logger = membership_member_detail.LOG
        membership_member_detail.LOG = logger_mock
        response = self.testapp.get('/members/1', status=200)
        membership_member_detail.LOG = logger

        # 1.1. At least contain name and address
        body = response.decode('utf8')
        self.assertTrue(self.member.firstname in body)
        self.assertTrue('SomeFirstnäme' in body)
        self.assertTrue(self.member.lastname in body)
        self.assertTrue('SomeLastnäme' in body)
        self.assertTrue(self.member.address1 in body)
        self.assertTrue('addr one' in body)
        self.assertTrue(self.member.address2 in body)
        self.assertTrue('addr two' in body)
        self.assertTrue(self.member.postcode in body)
        self.assertTrue('12345' in body)
        self.assertTrue(self.member.city in body)
        self.assertTrue('Footown Mäh' in body)

        # 1.2. Access is logged
        logger_mock.info.assert_called_with(
            'member details of membership number %s checked by %s',
            1,
            'rut')

        # 2. Verification fails if not a number
        self.assert_get_redirect_flash(
            '/members/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 3. Verification fails if membership number not found
        self.assert_get_redirect_flash(
            '/members/123',
            '/dashboard',
            'danger',
            'Membership number 123 does not exist.')

        # 4. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/members/1')

    def test_member_detail(self):
        """
        Test the member_detail view

        1. Get member details

           1. At least contain name and address
           2. Access is logged

        2. Verification fails if not a number
        3. Verification fails if membership number not found
        4. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Get member details
        logger_mock = Mock()
        logger = membership_member_detail.LOG
        membership_member_detail.LOG = logger_mock
        response = self.testapp.get('/detail/1', status=200)
        membership_member_detail.LOG = logger

        # 1.1. At least contain name and address
        body = response.decode('utf8')
        self.assertTrue(self.member.firstname in body)
        self.assertTrue('SomeFirstnäme' in body)
        self.assertTrue(self.member.lastname in body)
        self.assertTrue('SomeLastnäme' in body)
        self.assertTrue(self.member.address1 in body)
        self.assertTrue('addr one' in body)
        self.assertTrue(self.member.address2 in body)
        self.assertTrue('addr two' in body)
        self.assertTrue(self.member.postcode in body)
        self.assertTrue('12345' in body)
        self.assertTrue(self.member.city in body)
        self.assertTrue('Footown Mäh' in body)

        # 1.2. Access is logged
        logger_mock.info.assert_called_with(
            'member details of id %s checked by %s',
            1,
            'rut')

        # 2. Verification fails if not a number
        self.assert_get_redirect_flash(
            '/detail/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 3. Verification fails if membership number not found
        self.assert_get_redirect_flash(
            '/detail/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist.')

        # 4. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/detail/1')
