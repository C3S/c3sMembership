# -*- coding: utf-8 -*-

from unittest import mock
from datetime import date

from unittest import TestCase

from c3smembership.business.share_acquisition import (
    ShareAcquisition,
)


class ShareAcquisitionTest(TestCase):

    def test_create(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.create.side_effect = [
            'create result 1',
            'create result 2',
            'create result 3']

        share_acquisition = ShareAcquisition(share_repository_mock)

        self.assertEqual(
            share_acquisition.create('ABCD1234', 12),
            'create result 1')
        share_repository_mock.create.assert_called_with(
            'ABCD1234', 12, None)

        self.assertEqual(
            share_acquisition.create('WXYZ6789', 54, date(2017, 7, 20)),
            'create result 2')
        share_repository_mock.create.assert_called_with(
            'WXYZ6789', 54, date(2017, 7, 20))

        self.assertEqual(
            share_acquisition.create('ZZZZ9999', 60, None),
            'create result 3')

        # quantity_count must be integer
        with self.assertRaises(ValueError):
            share_acquisition.create('AAAA1111', 1.1)

        # quantity count must be at least 1
        with self.assertRaises(ValueError):
            share_acquisition.create('AAAA1111', 0)

        # quantity count must be at least 1
        with self.assertRaises(ValueError):
            share_acquisition.create('AAAA1111', -10)

        # quantity count must be at most 60
        with self.assertRaises(ValueError):
            share_acquisition.create('AAAA1111', 61)

    def test_set_signature_reception(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.set_signature_reception.side_effect = [
            'set_signature_reception result']

        share_acquisition = ShareAcquisition(share_repository_mock)
        share_id = 1
        reception_date = date(2017, 8, 24)

        share_acquisition.set_signature_reception(share_id, reception_date)

        share_repository_mock.set_signature_reception.assert_called_with(
            share_id, reception_date)

    def test_set_payment_confirmation(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.set_payment_confirmation.side_effect = [
            'set_payment_confirmation result']

        share_acquisition = ShareAcquisition(share_repository_mock)
        share_id = 1
        payment_date = date(2017, 8, 24)

        share_acquisition.set_payment_confirmation(share_id, payment_date)

        share_repository_mock.set_payment_confirmation.assert_called_with(
            share_id, payment_date)

    def test_set_reference_code(self):
        share_repository_mock = mock.Mock()
        share_repository_mock.set_reference_code.side_effect = [
            'set_reference_code result']

        share_acquisition = ShareAcquisition(share_repository_mock)
        share_id = 1
        reference_code = 'some dummy reference code'

        share_acquisition.set_reference_code(share_id, reference_code)

        share_repository_mock.set_reference_code.assert_called_with(
            share_id, reference_code)
