# -*- coding: utf-8 -*-

import mock
from datetime import (
    date,
    datetime,
)

from unittest import TestCase

import c3smembership.business.membership_application as \
    membership_application_package
from c3smembership.business.membership_application import (
    MembershipApplication,
)


class MemberApplicationTest(TestCase):

    def test_get(self):
        member_repository_mock = mock.Mock()
        member_mock = mock.Mock(
            membership_type='membership_type value',
            num_shares='num_shares value',
            date_of_submission='date_of_submission value',
            email_confirm_code='email_confirm_code value')
        member_repository_mock.get_member_by_id.side_effect = [member_mock]

        membership_application = MembershipApplication(member_repository_mock)
        data = membership_application.get('call1')

        member_repository_mock.get_member_by_id.assert_called_with('call1')
        self.assertEqual(data['membership_type'], 'membership_type value')
        self.assertEqual(data['shares_quantity'], 'num_shares value')
        self.assertEqual(data['date_of_submission'], 'date_of_submission value')
        self.assertEqual(data['payment_token'], 'email_confirm_code value')

    def test_set_signature_status(self):
        # general setup
        member_repository_mock = mock.Mock()
        member_mock = mock.Mock(
            signature_received_date=None,
            signature_received=None)
        member_repository_mock.get_member_by_id.side_effect = [
            member_mock,
            member_mock]
        membership_application = MembershipApplication(member_repository_mock)

        # function call
        membership_application.set_signature_status('member id 1', False)

        # check
        member_repository_mock.get_member_by_id.assert_called_with(
            'member id 1')
        self.assertFalse(member_mock.signature_received)
        self.assertEqual(
            member_mock.signature_received_date,
            datetime(1970, 1, 1))

        # setup
        datetime_mock = mock.Mock()
        datetime_mock.now.side_effect = ['now result']
        membership_application.datetime = datetime_mock

        # function call
        membership_application.set_signature_status('member id 2', True)

        # check
        member_repository_mock.get_member_by_id.assert_called_with(
            'member id 2')
        self.assertTrue(member_mock.signature_received)
        self.assertEqual(
            member_mock.signature_received_date,
            'now result')

    def test_get_signature_status(self):
        member_repository_mock = mock.Mock()
        member_mock = mock.Mock(signature_received='signature received value')
        member_repository_mock.get_member_by_id.side_effect = [member_mock]
        membership_application = MembershipApplication(member_repository_mock)

        signature_status = membership_application.get_signature_status(
            'member id')

        member_repository_mock.get_member_by_id.assert_called_with('member id')
        self.assertEqual(signature_status, 'signature received value')

    def test_set_payment_status(self):
        # general setup
        member_repository_mock = mock.Mock()
        member_mock = mock.Mock(
            payment_received_date=None,
            payment_received=None)
        member_repository_mock.get_member_by_id.side_effect = [
            member_mock,
            member_mock]
        membership_application = MembershipApplication(member_repository_mock)

        # function call
        membership_application.set_payment_status('member id 1', False)

        # check
        member_repository_mock.get_member_by_id.assert_called_with(
            'member id 1')
        self.assertFalse(member_mock.payment_received)
        self.assertEqual(
            member_mock.payment_received_date,
            datetime(1970, 1, 1))

        # setup
        datetime_mock = mock.Mock()
        datetime_mock.now.side_effect = ['now result']
        membership_application.datetime = datetime_mock

        # function call
        membership_application.set_payment_status('member id 2', True)

        # check
        member_repository_mock.get_member_by_id.assert_called_with(
            'member id 2')
        self.assertTrue(member_mock.payment_received)
        self.assertEqual(
            member_mock.payment_received_date,
            'now result')

    def test_get_payment_status(self):
        member_repository_mock = mock.Mock()
        member_mock = mock.Mock(payment_received='payment received value')
        member_repository_mock.get_member_by_id.side_effect = [member_mock]
        membership_application = MembershipApplication(member_repository_mock)

        payment_status = membership_application.get_payment_status(
            'member id')

        member_repository_mock.get_member_by_id.assert_called_with('member id')
        self.assertEqual(payment_status, 'payment received value')
