# -*- coding: utf-8 -*-

import mock
import os

from unittest import TestCase

from c3smembership.business.dues_invoice_archiving import (
    DuesInvoiceArchiving,
    IDuesInvoiceArchiving,
)


class DuesInvoiceArchivingTest(TestCase):

    def setUp(self):
        self.invoices = [
            mock.Mock(invoice_no_string='Dues15-0001', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0002', is_reversal=True),
            mock.Mock(invoice_no_string='Dues15-0003', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0004', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0005', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0006', is_reversal=False),
        ]
        self.members = [
            mock.Mock(membership_number=1),
            mock.Mock(membership_number=2),
        ]
        file1 = mock.Mock()
        type(file1).name = mock.PropertyMock(return_value='tmp1.pdf')
        file2 = mock.Mock()
        type(file2).name = mock.PropertyMock(return_value='tmp2.pdf')
        file3 = mock.Mock()
        type(file3).name = mock.PropertyMock(return_value='tmp3.pdf')
        file4 = mock.Mock()
        type(file4).name = mock.PropertyMock(return_value='tmp4.pdf')
        file5 = mock.Mock()
        type(file5).name = mock.PropertyMock(return_value='tmp5.pdf')
        self.files = [file1, file2, file3, file4, file5]

        self.isdir_patcher = mock.patch('os.path.isdir')
        self.isdir_mock = self.isdir_patcher.start()

        self.isfile_patcher = mock.patch('os.path.isfile')
        self.isfile_mock = self.isfile_patcher.start()

        self.copyfile_patcher = mock.patch('shutil.copyfile')
        self.copyfile_mock = self.copyfile_patcher.start()

        self.makedirs_patcher = mock.patch('os.makedirs')
        self.makedirs_mock = self.makedirs_patcher.start()

    def create_db_session(self, members=None):
        if members is None:
            members = []
        db_session = mock.Mock()
        query_result = mock.Mock()
        query_result.all.return_value = members
        db_session.query.return_value = query_result
        return db_session

    def create_make_invoice(self, files=None):
        if files is None:
            files = []
        make_invoice_mock = mock.Mock()
        make_invoice_mock.side_effect = files
        return make_invoice_mock

    def create_dues_invoice_repo_invoices(self, invoices=None):
        if invoices is None:
            invoices = []
        dues_invoice_repo_mock = mock.Mock()
        dues_invoice_repo_mock.get_by_membership_number.side_effect = invoices
        return dues_invoice_repo_mock

    def test_generate_missing_invoice_pdfs(self):
        self.isfile_mock.side_effect = [
            False, False, False, True, False, False]
        make_invoice_mock = self.create_make_invoice([
            self.files[0],
            self.files[2],
            self.files[3],
            self.files[4]])
        make_reversal_mock = self.create_make_invoice([self.files[1]])
        db_session = self.create_db_session(self.members)
        dues15_invoices_mock = self.create_dues_invoice_repo_invoices([
            [self.invoices[0], self.invoices[1]],
            [
                self.invoices[2], self.invoices[3], self.invoices[4],
                self.invoices[5]
            ],
        ])

        archiving = DuesInvoiceArchiving(
            db_session,
            'c3s_member',
            dues15_invoices_mock,
            make_invoice_mock,
            make_reversal_mock,
            '/tmp/invoices/archive'
        )
        generated_files = archiving.generate_missing_invoice_pdfs(4)

        self.assertEqual(len(generated_files), 4)
        self.assertEqual(
            generated_files,
            ['Dues15-0001', 'Dues15-0002', 'Dues15-0003', 'Dues15-0005']
        )
        self.isdir_mock.assert_called_with('/tmp/invoices/archive')
        self.copyfile_mock.assert_has_calls([
            mock.call('tmp1.pdf', '/tmp/invoices/archive/Dues15-0001.pdf'),
            mock.call('tmp2.pdf', '/tmp/invoices/archive/Dues15-0002.pdf'),
            mock.call('tmp3.pdf', '/tmp/invoices/archive/Dues15-0003.pdf'),
            mock.call('tmp4.pdf', '/tmp/invoices/archive/Dues15-0005.pdf'),
        ])
        make_invoice_mock.assert_has_calls([
            mock.call(self.members[0], self.invoices[0]),
            mock.call(self.members[1], self.invoices[2]),
            mock.call(self.members[1], self.invoices[4])
        ])
        self.assertEqual(make_invoice_mock.call_count, 3)
        make_reversal_mock.assert_has_calls([
            mock.call(self.members[0], self.invoices[1]),
        ])
        self.assertEqual(make_reversal_mock.call_count, 1)

    def test_archive_directory_creation(self):
        db_session = self.create_db_session()
        dues15_invoices_mock = self.create_dues_invoice_repo_invoices()
        make_invoice_mock = self.create_make_invoice()
        make_reversal_mock = self.create_make_invoice()

        self.isdir_mock.side_effect = [True]
        archiving = DuesInvoiceArchiving(
            db_session,
            'c3s_member',
            dues15_invoices_mock,
            make_invoice_mock,
            make_reversal_mock,
            '/tmp/invoices/archive'
        )
        self.makedirs_mock.assert_not_called()

        self.isdir_mock.side_effect = [False]
        DuesInvoiceArchiving(
            db_session,
            'c3s_member',
            dues15_invoices_mock,
            make_invoice_mock,
            make_reversal_mock,
            '/tmp/invoices/archive'
        )
        self.makedirs_mock.assert_called_with('/tmp/invoices/archive')

    def tearDown(self):
        self.isdir_patcher.stop()
        self.isfile_patcher.stop()
        self.copyfile_patcher.stop()
        self.makedirs_patcher.stop()
