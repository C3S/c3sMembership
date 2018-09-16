# -*- coding: utf-8  -*-
"""
Tests the c3smembership.data.repository.general_assembly_repository package.
"""

from datetime import (
    date,
    datetime,
)
import unittest

from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository


class TestGeneralAssemblyRepository(unittest.TestCase):
    """
    Tests the GeneralAssemblyRepository class.
    """

    def setUp(self):
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'member1@example.com',
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
            member2 = C3sMember(
                firstname=u'AAASomeFirstnäme',
                lastname=u'XXXSomeLastnäme',
                email=u'member2@example.com',
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
                firstname=u'Not invited',
                lastname=u'at all',
                email=u'member3@example.com',
                address1=u'Some',
                address2=u'Address',
                postcode=u'45678',
                city=u'Hamburg',
                country=u'Germany',
                locale=u'DE',
                date_of_birth=date(1980, 1, 2),
                email_is_confirmed=False,
                email_confirm_code=u'member3',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=45,
            )
            member1.membership_number = u'member_1'
            member1.membership_date = date(2018, 1, 1)
            member1.membership_accepted = True
            member1.email_invite_date_bcgv18 = datetime(2018, 9, 1, 23, 5, 15)
            member1.email_invite_flag_bcgv18 = True
            member1.email_invite_token_bcgv18 = u'test_token_1'
            DBSession.add(member1)
            member2.membership_number = u'member_2'
            member2.membership_date = date(2017, 1, 1)
            member2.membership_accepted = True
            member2.email_invite_date_bcgv18 = datetime(2018, 9, 2, 22, 3, 10)
            member2.email_invite_flag_bcgv18 = True
            member2.email_invite_token_bcgv18 = u'test_token_2'
            DBSession.add(member2)
            member3.membership_number = u'member_3'
            member3.membership_date = date(2016, 1, 1)
            member3.membership_accepted = True
            DBSession.add(member3)
            DBSession.flush()

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()

    def test_get_invitees(self):
        invitees = GeneralAssemblyRepository.get_invitees(1)
        self.assertEqual(len(invitees), 1)
        self.assertEqual(invitees[0].membership_number, 'member_3')

        invitees = GeneralAssemblyRepository.get_invitees(10)
        self.assertEqual(len(invitees), 1)

    def test_get_member_by_token(self):
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_1')
        self.assertEqual(member.membership_number, u'member_1')

        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        self.assertEqual(member.membership_number, u'member_2')

    def test_get_member_invitations(self):
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_1')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(u'member_1', member.membership_date)
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0]['number'], '5')
        self.assertEqual(
            invitations[0]['flag'],
            True)
        self.assertEqual(
            invitations[0]['sent'],
            datetime(2018, 9, 1, 23, 5, 15))

        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(u'member_2', member.membership_date)
        self.assertEqual(len(invitations), 2)
        self.assertEqual(invitations[0]['number'], '4')
        self.assertEqual(
            invitations[0]['flag'],
            False)

        # Test membership loss
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(
                u'member_2',
                member.membership_date,
                date(2017, 12, 31))
        self.assertEqual(len(invitations), 1)
        self.assertEqual(invitations[0]['number'], '4')
        self.assertEqual(
            invitations[0]['flag'],
            False)

    def test_get_member_invitation(self):
        invitation = GeneralAssemblyRepository.get_member_invitation(
            'member_1', '5')
        self.assertEqual(invitation['number'], '5')
        self.assertEqual(
            invitation['flag'],
            True)
        self.assertEqual(
            invitation['sent'],
            datetime(2018, 9, 1, 23, 5, 15))

        invitation = GeneralAssemblyRepository.get_member_invitation(
            'member_2', '4')
        self.assertEqual(invitation['number'], '4')
        self.assertEqual(
            invitation['flag'],
            False)

    def test_invite_member(self):
        member = C3sMember.get_by_id(3)

        # Invitation for 2014
        self.assertEquals(member.email_invite_flag_bcgv14, False)
        self.assertEquals(
            member.email_invite_date_bcgv14,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            '1',  # 2014
            None)
        self.assertEquals(member.email_invite_flag_bcgv14, True)
        self.assertTrue(
            member.email_invite_date_bcgv14 > datetime(1970, 1, 1, 0, 0))

        # Invitation for 2015
        self.assertEquals(member.email_invite_flag_bcgv15, False)
        self.assertEquals(member.email_invite_token_bcgv15, None)
        self.assertEquals(
            member.email_invite_date_bcgv15,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            '2',  # 2015
            u'token15')
        self.assertEquals(member.email_invite_flag_bcgv15, True)
        self.assertEquals(member.email_invite_token_bcgv15, u'token15')
        self.assertTrue(
            member.email_invite_date_bcgv15 > datetime(1970, 1, 1, 0, 0))

        # Invitation for 2016
        self.assertEquals(member.email_invite_flag_bcgv16, False)
        self.assertEquals(member.email_invite_token_bcgv16, None)
        self.assertEquals(
            member.email_invite_date_bcgv16,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            '3',  # 2016
            u'token16')
        self.assertEquals(member.email_invite_flag_bcgv16, True)
        self.assertEquals(member.email_invite_token_bcgv16, u'token16')
        self.assertTrue(
            member.email_invite_date_bcgv16 > datetime(1970, 1, 1, 0, 0))

        # Invitation for 2017
        self.assertEquals(member.email_invite_flag_bcgv17, False)
        self.assertEquals(member.email_invite_token_bcgv17, None)
        self.assertEquals(
            member.email_invite_date_bcgv17,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            '4',  # 2017
            u'token17')
        self.assertEquals(member.email_invite_flag_bcgv17, True)
        self.assertEquals(member.email_invite_token_bcgv17, u'token17')
        self.assertTrue(
            member.email_invite_date_bcgv17 > datetime(1970, 1, 1, 0, 0))

        # Invitation for 2018
        self.assertEquals(member.email_invite_flag_bcgv18, False)
        self.assertEquals(member.email_invite_token_bcgv18, None)
        self.assertEquals(
            member.email_invite_date_bcgv18,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            '5',  # 2018
            u'token18')
        self.assertEquals(member.email_invite_flag_bcgv18, True)
        self.assertEquals(member.email_invite_token_bcgv18, u'token18')
        self.assertTrue(
            member.email_invite_date_bcgv18 > datetime(1970, 1, 1, 0, 0))
