# -*- coding: utf-8  -*-
"""
Tests for the C3sMember anonymization.

Anonymization must clear all personal data but keep the statutory ledger
data which is subject to retention according to GenG §30, HGB §257 and
AO §147.
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


def create_member(email_confirm_code):
    """
    Create a C3sMember dataset for testing.
    """
    member = C3sMember(
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
        date_of_submission=date.today(),
        membership_type=u'normal',
        member_of_colsoc=True,
        name_of_colsoc=u'GEMA',
        num_shares=5,
    )
    member.accountant_comment = u'some note'
    member.court_of_law = u'Amtsgericht Foo'
    member.registration_number = u'HRB 12345'
    member.certificate_token = u'CERTTOKEN'
    member.mtype_confirm_token = u'MTYPETOKEN'
    member.email_confirm_token = u'EMAILTOKEN' + email_confirm_code
    member.membership_accepted = True
    member.membership_date = date(2014, 1, 1)
    member.membership_number = None
    member.membership_loss_date = date(2015, 12, 31)
    member.membership_loss_type = u'resignation'
    return member


class TestC3sMemberAnonymize(unittest.TestCase):
    """
    Tests the C3sMember.anonymize method.
    """

    def setUp(self):
        engine = engine_from_config({'sqlalchemy.url': 'sqlite:///:memory:'})
        DBSession.configure(bind=engine)
        self.db_session = DBSession()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.db_session.close()
        DBSession.remove()

    def test_anonymize_clears_personal_data(self):
        """
        Anonymization clears all personal data fields.
        """
        member = create_member(u'ABCDEFGH')
        member.membership_number = 42
        with transaction.manager:
            self.db_session.add(member)

        member = C3sMember.get_by_id(1)
        member.anonymize()

        self.assertIsNone(member.firstname)
        self.assertIsNone(member.lastname)
        self.assertIsNone(member.email)
        self.assertIsNone(member.password)
        self.assertIsNone(member.address1)
        self.assertIsNone(member.address2)
        self.assertIsNone(member.postcode)
        self.assertIsNone(member.city)
        self.assertIsNone(member.date_of_birth)
        self.assertIsNone(member.locale)
        self.assertIsNone(member.accountant_comment)
        self.assertIsNone(member.name_of_colsoc)
        self.assertIsNone(member.court_of_law)
        self.assertIsNone(member.registration_number)
        self.assertIsNone(member.certificate_token)
        self.assertIsNone(member.mtype_confirm_token)
        self.assertIsNone(member.email_confirm_token)

    def test_anonymize_keeps_ledger_data(self):
        """
        Anonymization keeps the statutory ledger data.
        """
        member = create_member(u'ABCDEFGH')
        member.membership_number = 42
        with transaction.manager:
            self.db_session.add(member)

        member = C3sMember.get_by_id(1)
        member.anonymize()

        self.assertEqual(member.id, 1)
        self.assertEqual(member.membership_number, 42)
        self.assertEqual(member.membership_type, u'normal')
        self.assertTrue(member.membership_accepted)
        self.assertEqual(member.membership_date, date(2014, 1, 1))
        self.assertEqual(member.membership_loss_date, date(2015, 12, 31))
        self.assertEqual(member.membership_loss_type, u'resignation')
        self.assertEqual(member.country, u'Foocountry')
        self.assertEqual(member.num_shares, 5)

    def test_anonymize_rewrites_confirm_code(self):
        """
        The unique reference code is rewritten to a deterministic
        non-personal value and stays unique for several anonymized members.
        """
        with transaction.manager:
            self.db_session.add(create_member(u'CODE1'))
            self.db_session.add(create_member(u'CODE2'))

        with transaction.manager:
            member_one = C3sMember.get_by_id(1)
            member_two = C3sMember.get_by_id(2)
            member_one.anonymize()
            member_two.anonymize()

        member_one = C3sMember.get_by_id(1)
        member_two = C3sMember.get_by_id(2)
        self.assertEqual(member_one.email_confirm_code, u'ANON-1')
        self.assertEqual(member_two.email_confirm_code, u'ANON-2')

    def test_anonymize_sets_timestamp(self):
        """
        Anonymization sets the anonymized timestamp and the is_anonymized
        flag.
        """
        member = create_member(u'ABCDEFGH')
        with transaction.manager:
            self.db_session.add(member)

        member = C3sMember.get_by_id(1)
        self.assertFalse(member.is_anonymized)
        self.assertIsNone(member.anonymized)

        member.anonymize()

        self.assertTrue(member.is_anonymized)
        self.assertIsNotNone(member.anonymized)
