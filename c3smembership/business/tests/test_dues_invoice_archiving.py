# -*- coding: utf-8 -*-
"""
Test the c3smembership.business.dues_invoice_archiving package
"""

from unittest import TestCase

import mock

from c3smembership.business.dues_invoice_archiving import DuesInvoiceArchiving


class DuesInvoiceArchivingTest(TestCase):
    """
    Test the DuesInvoiceArchiving class
    """
    # pylint: disable=too-many-instance-attributes

    def setUp(self):
        """
        Set up the test case

        Prepare invoices, file mocks and patch system methods
        """
        self.invoices = [
            mock.Mock(invoice_no_string='Dues15-0001', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0002', is_reversal=True),
            mock.Mock(invoice_no_string='Dues15-0003', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0004', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0005', is_reversal=False),
            mock.Mock(invoice_no_string='Dues15-0006', is_reversal=False),
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

    @classmethod
    def create_make_invoice(cls, files=None):
        """
        Create a make_invoice mock returning the specified files

        Args:
            files: Array. The files to be returned.

        Return:
            Mock for make_invoice
        """
        if files is None:
            files = []
        make_invoice_mock = mock.Mock()
        make_invoice_mock.side_effect = files
        return make_invoice_mock

    @classmethod
    def create_dues_invoice_repo_invoices(cls, invoices=None):
        """
        Create a dues invoice repository mock returning the specified invoices

        Args:
            invoices: Array. The invoices to be returned by the repository's
                get_all method

        Return:
            A dues invoice repository mock which returns the specified invoices
            on call of the get_all method.
        """
        if invoices is None:
            invoices = []
        dues_invoice_repo_mock = mock.Mock()
        dues_invoice_repo_mock.get_all.side_effect = invoices
        return dues_invoice_repo_mock

    def test_generate_missing_invoice_pdfs(self):
        """
        Test generating missing invoice PDF files

        1. Test more invoices to generate than count
        2. Test less invoices to generate than count
        """
        # 1. Test more invoices to generate than count
        self.isfile_mock.side_effect = [
            False, False, False, True, False, False]
        make_invoice_mock = self.create_make_invoice([
            self.files[0],
            self.files[2],
            self.files[3],
            self.files[4]])
        make_reversal_mock = self.create_make_invoice([self.files[1]])
        dues15_invoices_mock = self.create_dues_invoice_repo_invoices([
            [
                self.invoices[0], self.invoices[1], self.invoices[2],
                self.invoices[3], self.invoices[4], self.invoices[5],
            ],
            [
                self.invoices[0], self.invoices[1], self.invoices[2],
                self.invoices[3], self.invoices[4], self.invoices[5],
            ],
        ])

        archiving = DuesInvoiceArchiving(
            dues15_invoices_mock,
            '/tmp/invoices/archive'
        )
        archiving.configure_year(2015, make_invoice_mock, make_reversal_mock)
        generated_files = archiving.generate_missing_invoice_pdfs(2015, 4)

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
            mock.call(self.invoices[0]),
            mock.call(self.invoices[2]),
            mock.call(self.invoices[4])
        ])
        self.assertEqual(make_invoice_mock.call_count, 3)
        make_reversal_mock.assert_has_calls([
            mock.call(self.invoices[1]),
        ])
        self.assertEqual(make_reversal_mock.call_count, 1)

        # 2. Test less invoices to generate than count
        self.isfile_mock.side_effect = [
            False, False, False, True, True, True]
        make_invoice_mock = self.create_make_invoice([
            self.files[0],
            self.files[2],
            self.files[3]])
        make_reversal_mock = self.create_make_invoice([self.files[1]])

        archiving = DuesInvoiceArchiving(
            dues15_invoices_mock,
            '/tmp/invoices/archive'
        )
        archiving.configure_year(2015, make_invoice_mock, make_reversal_mock)
        generated_files = archiving.generate_missing_invoice_pdfs(2015, 10)

        self.assertEqual(len(generated_files), 3)

    def test_archive_directory_creation(self):
        """
        Test that the archive directory is created if it does not exist
        """
        dues15_invoices_mock = self.create_dues_invoice_repo_invoices()
        make_invoice_mock = self.create_make_invoice()
        make_reversal_mock = self.create_make_invoice()

        self.isdir_mock.side_effect = [True]
        archiving = DuesInvoiceArchiving(
            dues15_invoices_mock,
            '/tmp/invoices/archive'
        )
        archiving.configure_year(2015, make_invoice_mock, make_reversal_mock)
        self.makedirs_mock.assert_not_called()

        self.isdir_mock.side_effect = [False]
        DuesInvoiceArchiving(
            dues15_invoices_mock,
            '/tmp/invoices/archive'
        )
        archiving.configure_year(2015, make_invoice_mock, make_reversal_mock)
        self.makedirs_mock.assert_called_with('/tmp/invoices/archive')

    def test_get_configured_years(self):
        """
        Test the get_configured_years method
        """
        archiving = DuesInvoiceArchiving(None, None)
        self.assertEqual(archiving.get_configured_years(), [])
        archiving.configure_year(2015, None, None)
        self.assertEqual(archiving.get_configured_years(), [2015])
        archiving.configure_year(2010, None, None)
        self.assertEqual(archiving.get_configured_years(), [2010, 2015])
        archiving.configure_year(2019, None, None)
        self.assertEqual(archiving.get_configured_years(), [2010, 2015, 2019])

    def test_get_archiving_stats(self):
        """
        Test the get_archiving_stats method
        """
        repository_mock = self.create_dues_invoice_repo_invoices([
            # 2015 total
            [
                self.invoices[0], self.invoices[1]
            ],
            # 2015 check missing
            [
                self.invoices[0], self.invoices[1]
            ],
            # 2016 total
            [
                self.invoices[0], self.invoices[1], self.invoices[2],
                self.invoices[3], self.invoices[4], self.invoices[5],
            ],
            # 2016 check missing
            [
                self.invoices[0], self.invoices[1], self.invoices[2],
                self.invoices[3], self.invoices[4], self.invoices[5],
            ],
        ])
        self.isfile_mock.side_effect = [
            # 2015 checks
            False, False,
            # 2016 checks
            False, True, False, True, False, False,
        ]
        archiving = DuesInvoiceArchiving(
            repository_mock,
            '/tmp/invoices/archive'
        )
        archiving.configure_year(2015, None, None)
        archiving.configure_year(2016, None, None)
        stats = archiving.get_archiving_stats()
        self.assertEqual(len(stats), 2)
        self.assertEqual(stats[0]['year'], 2015)
        self.assertEqual(stats[0]['total'], 2)
        self.assertEqual(stats[0]['archived'], 0)
        self.assertEqual(stats[0]['not_archived'], 2)
        self.assertEqual(stats[1]['year'], 2016)
        self.assertEqual(stats[1]['total'], 6)
        self.assertEqual(stats[1]['archived'], 2)
        self.assertEqual(stats[1]['not_archived'], 4)

    def tearDown(self):
        """
        Tear down the test case by unpatching system methods
        """
        self.isdir_patcher.stop()
        self.isfile_patcher.stop()
        self.copyfile_patcher.stop()
        self.makedirs_patcher.stop()
