# -*- coding: utf-8 -*-
"""
Test the c3smembership.business.data_protection module
"""

from datetime import (
    date,
    datetime,
)
from unittest import TestCase, mock

from c3smembership.business.data_protection import (
    DataProtection,
    NotAnErasureCandidateError,
)


class DataProtectionTest(TestCase):
    """
    Test the DataProtection class
    """

    def setUp(self):
        self.member_repository = mock.Mock()
        self.dues_invoice_repository = mock.Mock()
        self.dues_invoice_archiving = mock.Mock()
        self.data_protection = DataProtection(
            self.member_repository,
            self.dues_invoice_repository,
            self.dues_invoice_archiving)

    @staticmethod
    def create_candidate_member():
        """
        Create a member mock which is an erasure candidate.
        """
        return mock.Mock(
            id=1,
            is_anonymized=False,
            membership_accepted=True,
            membership_number=42,
            membership_loss_date=date(2010, 6, 30),
            date_of_submission=datetime(2009, 1, 1))

    def test_member_retention_cutoff(self):
        """
        The retention period is counted from the end of the year of the
        membership loss.
        """
        # A loss in 2015 must be kept until the end of 2025, i.e. the
        # cut-off on any day in 2026 is 2016-01-01.
        self.assertEqual(
            DataProtection.get_member_retention_cutoff(date(2026, 7, 17)),
            date(2016, 1, 1))
        self.assertEqual(
            DataProtection.get_member_retention_cutoff(date(2026, 1, 1)),
            date(2016, 1, 1))

    def test_application_retention_cutoff(self):
        """
        The application cut-off lies 18 months back, clamped to the first
        day of the month.
        """
        self.assertEqual(
            DataProtection.get_application_retention_cutoff(
                date(2026, 7, 17)),
            date(2025, 1, 1))
        self.assertEqual(
            DataProtection.get_application_retention_cutoff(
                date(2026, 1, 5)),
            date(2024, 7, 1))

    def test_get_erasure_candidates(self):
        """
        Candidates are retrieved from the repository with the calculated
        cut-off dates.
        """
        self.member_repository.get_lost_members_before.return_value = [
            'lost']
        self.member_repository.get_stale_applications_before.return_value = [
            'stale']

        candidates = self.data_protection.get_erasure_candidates()

        self.assertEqual(candidates['lost_members'], ['lost'])
        self.assertEqual(candidates['stale_applications'], ['stale'])
        self.member_repository.get_lost_members_before.assert_called_with(
            DataProtection.get_member_retention_cutoff())
        self.member_repository.get_stale_applications_before \
            .assert_called_with(
                DataProtection.get_application_retention_cutoff())

    def test_is_erasure_candidate(self):
        """
        Candidate detection covers lost members, stale applications and
        refuses everything else.
        """
        is_candidate = self.data_protection.is_erasure_candidate

        # nonexistent dataset
        self.assertFalse(is_candidate(None))

        # lost member past retention
        member = self.create_candidate_member()
        self.assertTrue(is_candidate(member))

        # lost member within retention
        member.membership_loss_date = date.today()
        self.assertFalse(is_candidate(member))

        # already anonymized
        member = self.create_candidate_member()
        member.is_anonymized = True
        self.assertFalse(is_candidate(member))

        # active member without loss date
        member = self.create_candidate_member()
        member.membership_loss_date = None
        self.assertFalse(is_candidate(member))

        # stale application
        application = self.create_candidate_member()
        application.membership_accepted = False
        application.membership_number = None
        application.membership_loss_date = None
        self.assertTrue(is_candidate(application))

        # recent application
        application.date_of_submission = datetime.now()
        self.assertFalse(is_candidate(application))

    def test_anonymize_member_refused(self):
        """
        Anonymization of a non-candidate is refused and nothing is
        changed.
        """
        member = self.create_candidate_member()
        member.membership_loss_date = None
        self.member_repository.get_member_by_id.return_value = member

        with self.assertRaises(NotAnErasureCandidateError):
            self.data_protection.anonymize_member(1, u'staffer1')

        member.anonymize.assert_not_called()
        self.dues_invoice_archiving.remove_archived_invoices \
            .assert_not_called()

    def test_anonymize_member(self):
        """
        Anonymization removes the archived invoice PDFs, clears the
        personal data from the invoice records and anonymizes the member.
        """
        member = self.create_candidate_member()
        self.member_repository.get_member_by_id.return_value = member
        invoice = mock.Mock(email=u'some@shri.de', token=u'SECRET')
        self.dues_invoice_repository.get_by_member_id.return_value = [
            invoice]
        self.dues_invoice_archiving.remove_archived_invoices.return_value = [
            u'C3S-dues2015-0001']

        result = self.data_protection.anonymize_member(1, u'staffer1')

        self.assertEqual(result, member)
        member.anonymize.assert_called_with()
        self.dues_invoice_repository.get_by_member_id.assert_called_with(1)
        self.dues_invoice_archiving.remove_archived_invoices \
            .assert_called_with([invoice])
        self.assertIsNone(invoice.email)
        self.assertIsNone(invoice.token)
