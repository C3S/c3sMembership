# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.member_repository package.
"""

from datetime import date
import unittest

from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.member_repository import MemberRepository


class TestMemberRepository(unittest.TestCase):
    """
    Tests the MemberRepository class.
    """

    def setUp(self):
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(  # german
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=35,
            )
            member2 = C3sMember(  # german
                firstname=u'AAASomeFirstnäme',
                lastname=u'XXXSomeLastnäme',
                email=u'some2@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"DE",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAR',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=45,
            )
            member3 = C3sMember(
                firstname=u'Not Approved',
                lastname=u'Member',
                email=u'not.approved@example.com',
                address1=u'Some Street 123',
                address2=u'',
                postcode=u"12345",
                city=u"Some City",
                country=u"Some Country",
                locale=u"DE",
                date_of_birth=date(1980, 1, 2),
                email_is_confirmed=False,
                email_confirm_code=u'NOT_APPROVED_MEMBER',
                password=u'not_approved_member',
                date_of_submission=date(1970, 1, 1),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u'',
                num_shares=7,
            )
            member4 = C3sMember(
                firstname=u'Membership',
                lastname=u'Lost',
                email=u'membership.lost@example.com',
                address1=u'Some Street 123',
                address2=u'',
                postcode=u"12345",
                city=u"Some City",
                country=u"Some Country",
                locale=u"DE",
                date_of_birth=date(1980, 1, 2),
                email_is_confirmed=False,
                email_confirm_code=u'MEMBERSHIP_LOST',
                password=u'not_approved_member',
                date_of_submission=date(1970, 1, 1),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u'',
                num_shares=7,
            )
            # pylint: disable=no-member
            DBSession.add(member1)
            # pylint: disable=no-member
            DBSession.add(member2)
            # pylint: disable=no-member
            DBSession.add(member3)
            # pylint: disable=no-member
            DBSession.add(member4)

            member1.membership_number = u'member1'
            member1.membership_date = date(2013, 1, 1)
            member1.membership_accepted = True
            member2.membership_number = u'member2'
            member2.membership_date = date(2013, 1, 5)
            member2.membership_accepted = True
            member3.payment_received_date = date(2016, 10, 11)
            member4.membership_number = u'member3'
            member4.membership_date = date(2014, 1, 5)
            member4.membership_accepted = True
            member4.membership_loss_date = date(2015, 12, 31)

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()

    def test_get_member(self):
        """
        Tests the MemberRepository.get_member method.
        """
        member1 = MemberRepository.get_member('member1')
        self.assertEqual(member1.membership_number, 'member1')

        member2 = MemberRepository.get_member('member2')
        self.assertEqual(member2.membership_number, 'member2')

    def test_get_member_by_id(self):
        """
        Tests the MemberRepository.get_member method.
        """
        member1 = MemberRepository.get_member_by_id(1)
        self.assertEqual(member1.id, 1)

        member2 = MemberRepository.get_member_by_id(2)
        self.assertEqual(member2.id, 2)

    def test_get_accepted_members(self):
        """
        Tests the MemberRepository.get_accepted_members method.
        """
        members = MemberRepository.get_accepted_members()
        self.assertEqual(len(members), 2)

        members = MemberRepository.get_accepted_members(date(1970, 1, 1))
        self.assertEqual(len(members), 0)

        members = MemberRepository.get_accepted_members(date(2012, 12, 31))
        self.assertEqual(len(members), 0)

        members = MemberRepository.get_accepted_members(date(2013, 1, 1))
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].membership_number, 'member1')

        members = MemberRepository.get_accepted_members(date(2013, 1, 4))
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].membership_number, 'member1')

        members = MemberRepository.get_accepted_members(date(2013, 1, 5))
        self.assertEqual(len(members), 2)
        membership_numbers = []
        for member in members:
            membership_numbers.append(member.membership_number)
        self.assertTrue('member1' in membership_numbers)
        self.assertTrue('member2' in membership_numbers)

        members = MemberRepository.get_accepted_members(date(2016, 4, 23))
        self.assertEqual(len(members), 2)
        membership_numbers = []
        for member in members:
            membership_numbers.append(member.membership_number)
        self.assertTrue('member1' in membership_numbers)
        self.assertTrue('member2' in membership_numbers)

    # pylint: disable=invalid-name
    def test_get_accepted_members_sorted(self):
        """
        Tests the MemberRepository.get_accepted_members_sorted method.
        """
        members = MemberRepository.get_accepted_members_sorted()
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].lastname, u'SomeLastnäme')
        self.assertEqual(members[1].lastname, u'XXXSomeLastnäme')

        members[0].lastname = u'Smith'
        members[1].lastname = u'Jones'
        members = MemberRepository.get_accepted_members_sorted()
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].lastname, u'Jones')
        self.assertEqual(members[1].lastname, u'Smith')

        members[0].lastname = u'Smith'
        members[0].firstname = u'Jane'
        members[1].lastname = u'Smith'
        members[1].firstname = u'Caroline'
        members = MemberRepository.get_accepted_members_sorted()
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].lastname, u'Smith')
        self.assertEqual(members[0].firstname, u'Caroline')
        self.assertEqual(members[1].lastname, u'Smith')
        self.assertEqual(members[1].firstname, u'Jane')

        members[0].lastname = u'Smith'
        members[0].firstname = u'Beatrice'
        members[1].lastname = u'Smith'
        members[1].firstname = u'Caroline'
        members = MemberRepository.get_accepted_members_sorted()
        self.assertEqual(len(members), 2)
        self.assertEqual(members[0].lastname, u'Smith')
        self.assertEqual(members[0].firstname, u'Beatrice')
        self.assertEqual(members[1].lastname, u'Smith')
        self.assertEqual(members[1].firstname, u'Caroline')

    def test_get_accepted_members_count(self):
        """
        Tests the MemberRepository.get_accepted_members_count method.
        """
        members_count = MemberRepository.get_accepted_members_count()
        self.assertEqual(members_count, 2)

        members_count = MemberRepository.get_accepted_members_count(
            date(1970, 1, 1))
        self.assertEqual(members_count, 0)

        members_count = MemberRepository.get_accepted_members_count(
            date(2012, 12, 31))
        self.assertEqual(members_count, 0)

        members_count = MemberRepository.get_accepted_members_count(
            date(2013, 1, 1))
        self.assertEqual(members_count, 1)

        members_count = MemberRepository.get_accepted_members_count(
            date(2013, 1, 4))
        self.assertEqual(members_count, 1)

        members_count = MemberRepository.get_accepted_members_count(
            date(2013, 1, 5))
        self.assertEqual(members_count, 2)

        # member4 got membership the day after
        members_count = MemberRepository.get_accepted_members_count(
            date(2014, 1, 4))
        self.assertEqual(members_count, 2)

        # member4 got membership that day
        members_count = MemberRepository.get_accepted_members_count(
            date(2014, 1, 5))
        self.assertEqual(members_count, 3)

        # member4 lost membership that day but is still member
        members_count = MemberRepository.get_accepted_members_count(
            date(2015, 12, 31))
        self.assertEqual(members_count, 3)

        # member4 lost membership the day before
        members_count = MemberRepository.get_accepted_members_count(
            date(2016, 1, 1))
        self.assertEqual(members_count, 2)

        members_count = MemberRepository.get_accepted_members_count(
            date(2016, 4, 23))
        self.assertEqual(members_count, 2)
