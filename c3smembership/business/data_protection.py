# -*- coding: utf-8 -*-
"""
Data protection erasure workflow.

Implements the retention policy of the DSGVO (GDPR) storage limitation
principle, Art. 5(1)(e), and the erasure obligation, Art. 17:

- Datasets of members who lost membership must be kept during the
  statutory retention periods (GenG §30, HGB §257, AO §147) and erased
  afterwards.
- Datasets of membership applications which were never completed have no
  legal basis to be kept beyond a processing period.

Erasure is implemented as anonymization: all personal data is cleared
while the statutory ledger data (membership number, shares, dues
aggregates) is kept. See C3sMember.anonymize.
"""

from datetime import date
import logging


LOG = logging.getLogger(__name__)

# Retention period for members who lost membership: accounting records
# must be kept for up to ten years according to HGB §257 and AO §147,
# counted from the end of the calendar year of the membership loss.
MEMBER_RETENTION_YEARS = 10

# Retention period for membership applications which never completed the
# acquisition process. There is no statutory retention obligation for
# them, so they must be erased once the application process can be
# considered abandoned, Art. 5(1)(e) DSGVO.
APPLICATION_RETENTION_MONTHS = 18


class NotAnErasureCandidateError(Exception):
    """
    Raised when a member dataset must not be anonymized.

    This is the case when the dataset is still within its retention
    period, still an active membership or already anonymized.
    """
    pass


class DataProtection(object):
    """
    Provides the erasure workflow: candidate determination and
    anonymization.
    """

    def __init__(self, member_repository, dues_invoice_repository,
                 dues_invoice_archiving):
        """
        Initialise the DataProtection object.

        Args:
            member_repository: The member repository used to determine
                erasure candidates.
            dues_invoice_repository: The dues invoice repository used to
                find the member's invoices.
            dues_invoice_archiving: The invoice archiving object used to
                remove archived invoice PDF files which contain personal
                data.
        """
        self._member_repository = member_repository
        self._dues_invoice_repository = dues_invoice_repository
        self._dues_invoice_archiving = dues_invoice_archiving

    @classmethod
    def get_member_retention_cutoff(cls, today=None):
        """
        Get the cut-off date for lost members.

        The retention period is counted from the end of the calendar year
        of the membership loss. Members whose membership loss date lies
        strictly before the returned date are past retention.

        Args:
            today: Optional. The date for which the cut-off is calculated.
                If not specified the system date is used.

        Returns:
            The cut-off date, i.e. January 1st of the year
            MEMBER_RETENTION_YEARS before the current year.
        """
        if today is None:
            today = date.today()
        return date(today.year - MEMBER_RETENTION_YEARS, 1, 1)

    @classmethod
    def get_application_retention_cutoff(cls, today=None):
        """
        Get the cut-off date for stale membership applications.

        Applications submitted strictly before the returned date are
        considered abandoned.

        Args:
            today: Optional. The date for which the cut-off is calculated.
                If not specified the system date is used.

        Returns:
            The cut-off date APPLICATION_RETENTION_MONTHS before today.
        """
        if today is None:
            today = date.today()
        month = today.month - APPLICATION_RETENTION_MONTHS - 1
        year = today.year + month // 12
        month = month % 12 + 1
        # Clamp to the first day of the month to avoid invalid dates like
        # February 30th. This errs on the safe side by keeping
        # applications a few days longer.
        return date(year, month, 1)

    def get_erasure_candidates(self):
        """
        Get the datasets whose retention period has expired.

        Returns:
            A dict with two entries:

            - 'lost_members': not yet anonymized members whose membership
              loss lies past the retention period,
            - 'stale_applications': not yet anonymized applications which
              never completed the acquisition process and were submitted
              before the application retention period.
        """
        return {
            'lost_members': self._member_repository.get_lost_members_before(
                self.get_member_retention_cutoff()),
            'stale_applications':
                self._member_repository.get_stale_applications_before(
                    self.get_application_retention_cutoff()),
        }

    def is_erasure_candidate(self, member):
        """
        Indicate whether the member dataset may be anonymized.

        Args:
            member: The C3sMember dataset to check.

        Returns:
            True if the dataset is a lost member past retention or a stale
            application, False otherwise.
        """
        if member is None or member.is_anonymized:
            return False
        if member.membership_loss_date is not None:
            return member.membership_loss_date < \
                self.get_member_retention_cutoff()
        if not member.membership_accepted and \
                member.membership_number is None:
            date_of_submission = member.date_of_submission
            if hasattr(date_of_submission, 'date'):
                date_of_submission = date_of_submission.date()
            return date_of_submission < \
                self.get_application_retention_cutoff()
        return False

    def anonymize_member(self, member_id, actor):
        """
        Anonymize the member dataset.

        Verifies that the dataset is an erasure candidate (defense in
        depth), removes the member's archived invoice PDF files, clears
        the personal data from the member's invoice records and anonymizes
        the member dataset. The operation is logged for accountability,
        Art. 5(2) DSGVO.

        Args:
            member_id: The technical ID of the member to anonymize.
            actor: The login of the staff user performing the
                anonymization.

        Raises:
            NotAnErasureCandidateError: In case the dataset must not be
                anonymized.

        Returns:
            The anonymized member dataset.
        """
        member = self._member_repository.get_member_by_id(member_id)
        if not self.is_erasure_candidate(member):
            LOG.warning(
                'anonymization of member id %s refused: not an erasure '
                'candidate. Requested by %s.', member_id, actor)
            raise NotAnErasureCandidateError(
                'Member id {} is not an erasure candidate and was not '
                'anonymized.'.format(member_id))

        invoices = self._dues_invoice_repository.get_by_member_id(member.id)
        removed_files = self._dues_invoice_archiving \
            .remove_archived_invoices(invoices)
        for invoice in invoices:
            invoice.email = None
            invoice.token = None
        member.anonymize()
        LOG.info(
            'member id %s was anonymized by %s, %s archived invoice PDFs '
            'removed.', member_id, actor, len(removed_files))
        return member
