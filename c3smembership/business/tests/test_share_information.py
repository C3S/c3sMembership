# -*- coding: utf-8 -*-

from datetime import date

from unittest import TestCase, mock

from c3smembership.business.share_information import (
    ShareInformation,
)


class ShareInformationTest(TestCase):

    def test_get_statistics(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.get_approved.side_effect = ['get_approved result']
        share_repository_mock.get_approved_count.side_effect = \
            ['get_approved_count result']
        share_repository_mock.get_paid_not_approved.side_effect = \
            ['get_paid_not_approved result']
        share_repository_mock.get_paid_not_approved_count.side_effect = \
            ['get_paid_not_approved_count result']

        share_information = ShareInformation(share_repository_mock)
        start_date = date(2017, 7, 19)
        end_date = date(2017, 7, 30)

        statistics = share_information.get_statistics(start_date, end_date)

        share_repository_mock.get_approved.assert_called_with(
            start_date, end_date)
        share_repository_mock.get_approved_count.assert_called_with(
            start_date, end_date)
        share_repository_mock.get_paid_not_approved.assert_called_with(
            start_date, end_date)
        share_repository_mock.get_paid_not_approved_count.assert_called_with(
            start_date, end_date)
        self.assertEqual(
            statistics['approved_shares'],
            'get_approved result')
        self.assertEqual(
            statistics['approved_shares_count'],
            'get_approved_count result')
        self.assertEqual(
            statistics['paid_not_approved_shares'],
            'get_paid_not_approved result')
        self.assertEqual(
            statistics['paid_not_approved_shares_count'],
            'get_paid_not_approved_count result')

    def test_get_share_count(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.get_share_count.side_effect = [
            'get_share_count result 1',
            'get_share_count result 2']

        share_information = ShareInformation(share_repository_mock)

        self.assertEqual(
            share_information.get_share_count(),
            'get_share_count result 1')
        share_repository_mock.get_share_count.assert_called_with(None)

        self.assertEqual(
            share_information.get_share_count(date(2017, 7, 20)),
            'get_share_count result 2')
        share_repository_mock.get_share_count.assert_called_with(
            date(2017, 7, 20))

    def test_get_member_share_count(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.get_member_share_count.side_effect = [
            'get_member_share_count result 1',
            'get_member_share_count result 2']

        share_information = ShareInformation(share_repository_mock)

        self.assertEqual(
            share_information.get_member_share_count('ABCD1234'),
            'get_member_share_count result 1')
        share_repository_mock.get_member_share_count.assert_called_with(
            'ABCD1234', None)

        self.assertEqual(
            share_information.get_member_share_count(
                'WXYZ6789', date(2017, 7, 20)),
            'get_member_share_count result 2')
        share_repository_mock.get_member_share_count.assert_called_with(
            'WXYZ6789', date(2017, 7, 20))

    def test_get(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.get.side_effect = ['get result']

        share_information = ShareInformation(share_repository_mock)

        self.assertEqual(share_information.get(1), 'get result')
        share_repository_mock.get.assert_called_with(1)

    def test_delete(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.delete.side_effect = ['delete result']

        share_information = ShareInformation(share_repository_mock)

        self.assertEqual(share_information.delete(2), 'delete result')
        share_repository_mock.delete.assert_called_with(2)

    def test_get_member_shares(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.get_member_shares.side_effect = [
            'get_member_shares result']

        share_information = ShareInformation(share_repository_mock)

        self.assertEqual(
            share_information.get_member_shares('ABCD1234'),
            'get_member_shares result')
        share_repository_mock.get_member_shares.assert_called_with('ABCD1234')
