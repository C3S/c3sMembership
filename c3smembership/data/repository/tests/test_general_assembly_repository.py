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
from c3smembership.data.model.base.general_assembly import GeneralAssembly
from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository


GENERAL_ASSEMBLY_NUMBER_2014 = 1
GENERAL_ASSEMBLY_NUMBER_2015 = 2
GENERAL_ASSEMBLY_NUMBER_2015_2 = 3
GENERAL_ASSEMBLY_NUMBER_2016 = 4
GENERAL_ASSEMBLY_NUMBER_2017 = 5
GENERAL_ASSEMBLY_NUMBER_2018 = 6
GENERAL_ASSEMBLY_NUMBER_2018_2 = 7


class TestGeneralAssemblyRepository(unittest.TestCase):
    """
    Tests the GeneralAssemblyRepository class.
    """

    def setUp(self):
        """
        Set up tests
        """
        # pylint: disable=no-member
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
            member1.email_invite_date_bcgv18_2 = datetime(2018, 9, 1, 23, 5, 15)
            member1.email_invite_flag_bcgv18_2 = True
            member1.email_invite_token_bcgv18_2 = u'test_token_1'
            DBSession.add(member1)
            member2.membership_number = u'member_2'
            member2.membership_date = date(2017, 1, 1)
            member2.membership_accepted = True
            member2.email_invite_date_bcgv18_2 = datetime(2018, 9, 2, 22, 3, 10)
            member2.email_invite_flag_bcgv18_2 = True
            member2.email_invite_token_bcgv18_2 = u'test_token_2'
            DBSession.add(member2)
            member3.membership_number = u'member_3'
            member3.membership_date = date(2016, 1, 1)
            member3.membership_accepted = True
            DBSession.add(member3)

            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2014,
                u'1. ordentliche Generalversammlung',
                date(2014, 8, 23)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2015,
                u'2. ordentliche Generalversammlung',
                date(2015, 6, 13)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2015_2,
                u'Außerordentliche Generalversammlung',
                date(2015, 7, 16)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2016,
                u'3. ordentliche Generalversammlung',
                date(2016, 4, 17)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2017,
                u'4. ordentliche Generalversammlung',
                date(2017, 4, 2)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2018,
                u'5. ordentliche Generalversammlung',
                date(2018, 6, 3)))
            DBSession.add(GeneralAssembly(
                GENERAL_ASSEMBLY_NUMBER_2018_2,
                u'Außerordentliche Generalversammlung',
                date(2018, 12, 1)))

            DBSession.flush()

    def tearDown(self):
        """
        Tear down the set setup
        """
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()

    def test_get_invitees(self):
        """
        Test the get_invitees method
        """
        invitees = GeneralAssemblyRepository.get_invitees(1)
        self.assertEqual(len(invitees), 1)
        self.assertEqual(invitees[0].membership_number, 'member_3')

        invitees = GeneralAssemblyRepository.get_invitees(10)
        self.assertEqual(len(invitees), 1)

    def test_get_member_by_token(self):
        """
        Test the get_member_by_token method
        """
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_1')
        self.assertEqual(member.membership_number, u'member_1')

        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        self.assertEqual(member.membership_number, u'member_2')

    def test_get_member_invitations(self):
        """
        Test the get_member_invitations method

        1. Test invited
        2. Test not invited
        3. Test membership loss
        """
        # 1. Test invited
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_1')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(u'member_1', member.membership_date)
        self.assertEqual(len(invitations), 2)
        self.assertEqual(
            invitations[0]['number'], GENERAL_ASSEMBLY_NUMBER_2018)
        self.assertEqual(
            invitations[0]['flag'],
            False)
        self.assertEqual(
            invitations[0]['sent'],
            datetime(1970, 1, 1, 0, 0))
        self.assertEqual(
            invitations[1]['number'], GENERAL_ASSEMBLY_NUMBER_2018_2)
        self.assertEqual(
            invitations[1]['flag'],
            True)
        self.assertEqual(
            invitations[1]['sent'],
            datetime(2018, 9, 1, 23, 5, 15))

        # 2. Test not invited
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(u'member_2', member.membership_date)
        self.assertEqual(len(invitations), 3)
        self.assertEqual(
            invitations[0]['number'], GENERAL_ASSEMBLY_NUMBER_2017)
        self.assertEqual(
            invitations[0]['flag'],
            False)

        # 3. Test membership loss
        member = GeneralAssemblyRepository.get_member_by_token(u'test_token_2')
        invitations = GeneralAssemblyRepository \
            .get_member_invitations(
                u'member_2',
                member.membership_date,
                date(2017, 12, 31))
        self.assertEqual(len(invitations), 1)
        self.assertEqual(
            invitations[0]['number'], GENERAL_ASSEMBLY_NUMBER_2017)
        self.assertEqual(
            invitations[0]['flag'],
            False)

    def test_get_member_invitation(self):
        """
        Test the get_member_invitation method
        """
        invitation = GeneralAssemblyRepository.get_member_invitation(
            'member_1', GENERAL_ASSEMBLY_NUMBER_2018_2)
        self.assertEqual(invitation['number'], GENERAL_ASSEMBLY_NUMBER_2018_2)
        self.assertEqual(
            invitation['flag'],
            True)
        self.assertEqual(
            invitation['sent'],
            datetime(2018, 9, 1, 23, 5, 15))

        invitation = GeneralAssemblyRepository.get_member_invitation(
            'member_2', GENERAL_ASSEMBLY_NUMBER_2017)
        self.assertEqual(invitation['number'], GENERAL_ASSEMBLY_NUMBER_2017)
        self.assertEqual(
            invitation['flag'],
            False)

    def test_invite_member(self):
        """
        Test the invite_member method

        1. Invitation for 2014
        2. Invitation for 2015
        3. Invitation for 2016
        4. Invitation for 2017
        5. Invitation for 2018
        """
        member = C3sMember.get_by_id(3)

        # 1. Invitation for 2014
        self.assertEquals(member.email_invite_flag_bcgv14, False)
        self.assertEquals(
            member.email_invite_date_bcgv14,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            GENERAL_ASSEMBLY_NUMBER_2014,
            None)
        self.assertEquals(member.email_invite_flag_bcgv14, True)
        self.assertTrue(
            member.email_invite_date_bcgv14 > datetime(1970, 1, 1, 0, 0))

        # 2. Invitation for 2015
        self.assertEquals(member.email_invite_flag_bcgv15, False)
        self.assertEquals(member.email_invite_token_bcgv15, None)
        self.assertEquals(
            member.email_invite_date_bcgv15,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            GENERAL_ASSEMBLY_NUMBER_2015,
            u'token15')
        self.assertEquals(member.email_invite_flag_bcgv15, True)
        self.assertEquals(member.email_invite_token_bcgv15, u'token15')
        self.assertTrue(
            member.email_invite_date_bcgv15 > datetime(1970, 1, 1, 0, 0))

        # 3. Invitation for 2016
        self.assertEquals(member.email_invite_flag_bcgv16, False)
        self.assertEquals(member.email_invite_token_bcgv16, None)
        self.assertEquals(
            member.email_invite_date_bcgv16,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            GENERAL_ASSEMBLY_NUMBER_2016,
            u'token16')
        self.assertEquals(member.email_invite_flag_bcgv16, True)
        self.assertEquals(member.email_invite_token_bcgv16, u'token16')
        self.assertTrue(
            member.email_invite_date_bcgv16 > datetime(1970, 1, 1, 0, 0))

        # 4. Invitation for 2017
        self.assertEquals(member.email_invite_flag_bcgv17, False)
        self.assertEquals(member.email_invite_token_bcgv17, None)
        self.assertEquals(
            member.email_invite_date_bcgv17,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            GENERAL_ASSEMBLY_NUMBER_2017,
            u'token17')
        self.assertEquals(member.email_invite_flag_bcgv17, True)
        self.assertEquals(member.email_invite_token_bcgv17, u'token17')
        self.assertTrue(
            member.email_invite_date_bcgv17 > datetime(1970, 1, 1, 0, 0))

        # 5. Invitation for 2018
        self.assertEquals(member.email_invite_flag_bcgv18, False)
        self.assertEquals(member.email_invite_token_bcgv18, None)
        self.assertEquals(
            member.email_invite_date_bcgv18,
            datetime(1970, 1, 1, 0, 0))
        GeneralAssemblyRepository.invite_member(
            'member_3',
            GENERAL_ASSEMBLY_NUMBER_2018,
            u'token18')
        self.assertEquals(member.email_invite_flag_bcgv18, True)
        self.assertEquals(member.email_invite_token_bcgv18, u'token18')
        self.assertTrue(
            member.email_invite_date_bcgv18 > datetime(1970, 1, 1, 0, 0))

    def test_get_general_assemblies(self):
        """
        Test the get_general_assemblies method

        1. Test count
        2. Test properties
        """
        general_assemblies = GeneralAssemblyRepository.get_general_assemblies()

        # 1. Test count
        self.assertEquals(len(general_assemblies), 7)

        # 2. Test properties
        self.assertEquals(
            general_assemblies[GENERAL_ASSEMBLY_NUMBER_2018 - 1].name,
            u'5. ordentliche Generalversammlung')
        self.assertEquals(
            general_assemblies[GENERAL_ASSEMBLY_NUMBER_2018 - 1].date,
            date(2018, 6, 3))
        self.assertEquals(
            general_assemblies[GENERAL_ASSEMBLY_NUMBER_2018 - 1].number,
            GENERAL_ASSEMBLY_NUMBER_2018)

    def test_get_general_assembly(self):
        """
        Test the get_general_assembly method

        1. Test existing general assemblies
        2. Test properties
        3. Test non-existing general assembly
        3. Test invalid number type
        """
        # 1. Test existing general assemblies
        general_assembly = GeneralAssemblyRepository.get_general_assembly(
            GENERAL_ASSEMBLY_NUMBER_2014)
        self.assertEqual(general_assembly.number, GENERAL_ASSEMBLY_NUMBER_2014)
        general_assembly = GeneralAssemblyRepository.get_general_assembly(
            GENERAL_ASSEMBLY_NUMBER_2015)
        self.assertEqual(general_assembly.number, GENERAL_ASSEMBLY_NUMBER_2015)
        general_assembly = GeneralAssemblyRepository.get_general_assembly(
            GENERAL_ASSEMBLY_NUMBER_2018)
        self.assertEqual(general_assembly.number, GENERAL_ASSEMBLY_NUMBER_2018)

        # 2. Test properties
        general_assembly = GeneralAssemblyRepository.get_general_assembly(
            GENERAL_ASSEMBLY_NUMBER_2018)
        self.assertEquals(
            general_assembly.name,
            u'5. ordentliche Generalversammlung')
        self.assertEquals(general_assembly.date, date(2018, 6, 3))
        self.assertEquals(
            general_assembly.number,
            GENERAL_ASSEMBLY_NUMBER_2018)

        # 3. Test non-existing general assembly
        general_assembly = GeneralAssemblyRepository.get_general_assembly(0)
        self.assertIsNone(general_assembly)

        # 4. Test invalid number type
        with self.assertRaises(ValueError):
            GeneralAssemblyRepository.get_general_assembly('not an integer')
