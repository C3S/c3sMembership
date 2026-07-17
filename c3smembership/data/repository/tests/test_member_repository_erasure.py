# -*- coding: utf-8  -*-
"""
Tests the erasure candidate queries of the member repository.
"""

from datetime import date
import unittest

from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.member_repository import MemberRepository


def create_member(email_confirm_code, date_of_submission=None):
    """
    Create a C3sMember dataset for testing.
    """
    if date_of_submission is None:
        date_of_submission = date(2020, 1, 1)
    return C3sMember(
        firstname=u'SomeFirstnäme',
        lastname=u'SomeLastnäme',
        email=u'some@shri.de',
        address1=u'addr one',
        address2=u'addr two',
        postcode=u'12345',
        city=u'Footown Mäh',
        country=u'Foocountry',
        locale=u'DE',
        date_of_birth=date(1980, 1, 2),
        email_is_confirmed=False,
        email_confirm_code=email_confirm_code,
        password=u'arandompassword',
        date_of_submission=date_of_submission,
        membership_type=u'normal',
        member_of_colsoc=False,
        name_of_colsoc=u'',
        num_shares=1,
    )


class TestMemberRepositoryErasure(unittest.TestCase):
    """
    Tests the get_lost_members_before and get_stale_applications_before
    queries.
    """

    def setUp(self):
        engine = engine_from_config({'sqlalchemy.url': 'sqlite:///:memory:'})
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.db_session.close()
        DBSession.remove()

    def _add_lost_member(self, code, loss_date, anonymized=None):
        """
        Add an accepted member which lost membership.
        """
        member = create_member(code)
        member.membership_accepted = True
        member.membership_date = date(2010, 1, 1)
        member.membership_number = len(code)
        member.membership_loss_date = loss_date
        member.anonymized = anonymized
        self.db_session.add(member)

    def test_lost_members_boundary(self):
        """
        Only members whose loss date lies strictly before the cut-off date
        are returned.
        """
        with transaction.manager:
            # loss one day before the cut-off: past retention
            self._add_lost_member(u'A', date(2015, 12, 31))
            # loss exactly on the cut-off: retention not yet expired
            self._add_lost_member(u'BB', date(2016, 1, 1))
            # no loss: active member
            member = create_member(u'CCC')
            member.membership_accepted = True
            member.membership_number = 3
            self.db_session.add(member)

        result = MemberRepository.get_lost_members_before(date(2016, 1, 1))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].membership_loss_date, date(2015, 12, 31))

    def test_lost_members_excludes_anonymized(self):
        """
        Already anonymized members are not returned again.
        """
        with transaction.manager:
            self._add_lost_member(u'A', date(2010, 6, 30))
            self._add_lost_member(
                u'BB', date(2010, 6, 30), anonymized=date(2024, 1, 1))

        result = MemberRepository.get_lost_members_before(date(2016, 1, 1))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].email_confirm_code, u'A')

    def test_stale_applications_boundary(self):
        """
        Only applications submitted strictly before the cut-off date are
        returned.
        """
        with transaction.manager:
            self.db_session.add(
                create_member(u'OLD', date_of_submission=date(2024, 12, 31)))
            self.db_session.add(
                create_member(u'NEW', date_of_submission=date(2025, 1, 1)))

        result = MemberRepository.get_stale_applications_before(
            date(2025, 1, 1))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].email_confirm_code, u'OLD')

    def test_stale_applications_excludes_accepted_and_anonymized(self):
        """
        Accepted members and anonymized datasets never appear among the
        stale applications, duplicates do.
        """
        with transaction.manager:
            accepted = create_member(
                u'MEMBER', date_of_submission=date(2015, 1, 1))
            accepted.membership_accepted = True
            accepted.membership_number = 42
            self.db_session.add(accepted)

            anonymized = create_member(
                u'ANON-2', date_of_submission=date(2015, 1, 1))
            anonymized.anonymized = date(2024, 1, 1)
            self.db_session.add(anonymized)

            duplicate = create_member(
                u'DUP', date_of_submission=date(2015, 1, 1))
            duplicate.is_duplicate = True
            self.db_session.add(duplicate)

        result = MemberRepository.get_stale_applications_before(
            date(2025, 1, 1))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].email_confirm_code, u'DUP')
