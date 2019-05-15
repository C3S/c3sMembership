# -*- coding: utf-8 -*-

"""
Test the general assembly module
"""

from datetime import date
import unittest

import mock
from pyramid import testing
from pyramid_mailer import get_mailer
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
from c3smembership.data.repository.member_repository import MemberRepository
from c3smembership.business.member_information import MemberInformation
from c3smembership.business.general_assembly_invitation import \
    GeneralAssemblyInvitation
from c3smembership.presentation.views.general_assembly import (
    batch_invite,
    CURRENT_GENERAL_ASSEMBLY,
    general_assembly_invitation,
)


GENERAL_ASSEMBLY_NUMBER_2014 = 1
GENERAL_ASSEMBLY_NUMBER_2015 = 2
GENERAL_ASSEMBLY_NUMBER_2015_2 = 3
GENERAL_ASSEMBLY_NUMBER_2016 = 4
GENERAL_ASSEMBLY_NUMBER_2017 = 5
GENERAL_ASSEMBLY_NUMBER_2018 = 6
GENERAL_ASSEMBLY_NUMBER_2018_2 = 7


def init_testing_db():
    """
    Initializes the memory database with test samples.
    """

    my_settings = {
        'sqlalchemy.url': 'sqlite:///:memory:', }
    engine = engine_from_config(my_settings)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)

    with transaction.manager:
        # There is a side effect of test_initialization.py after which there
        # are still records in the database although it is setup from scratch.
        # Therefore, remove all members to have an empty table.

        # pylint: disable=no-member
        members = C3sMember.get_all()
        for member in members:
            DBSession.delete(member)
        DBSession.flush()

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

        # German person
        member1 = C3sMember(
            firstname=u'SomeFirstnäme',
            lastname=u'SomeLastnäme',
            email=u'some@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFG1',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'23',
        )
        # English person
        member2 = C3sMember(
            firstname=u'AAASomeFirstnäme',
            lastname=u'XXXSomeLastnäme',
            email=u'some2@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFG2',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'23',
        )
        # German legal entity
        member3 = C3sMember(
            firstname=u'Cooles PlattenLabel',
            lastname=u'SomeLastnäme',
            email=u'some@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFG3',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'42',
        )
        # English legal entity
        member4 = C3sMember(
            firstname=u'Incredible Records',
            lastname=u'XXXSomeLastnäme',
            email=u'some2@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFG4',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'2',
        )
        member1.membership_accepted = True
        member1.membership_number = u'11'
        DBSession.add(member1)
        member2.membership_accepted = True
        member2.membership_number = u'22'
        DBSession.add(member2)
        member3.membership_accepted = True
        member3.membership_number = u'33'
        DBSession.add(member3)
        member4.membership_accepted = True
        member4.membership_number = u'44'
        DBSession.add(member4)

        DBSession.flush()
    return DBSession


class TestInvitation(unittest.TestCase):
    """
    Tests the invitations.
    """

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.add_route('membership_listing_backend', '/memberships')
        self.config.add_route('toolbox', '/toolbox')
        self.config.add_route('dashboard', '/dashboard')
        self.config.add_route('general_assembly', '/general_assembly')
        self.config.add_route('general_assemblies', '/general_assemblies')
        self.config.add_route('member_details', '/members/{membership_number}')
        self.config.registry.settings['c3smembership.url'] = 'http://foo.com'
        self.config.registry.settings['ticketing.url'] = 'http://bar.com'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'test@example.com'

        self.config.registry.general_assembly_invitation = \
            GeneralAssemblyInvitation(GeneralAssemblyRepository())
        self.config.registry.general_assembly_invitation.date = mock.Mock()
        self.config.registry.member_information = MemberInformation(
            MemberRepository)
        self.session = init_testing_db()

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    def test_invitation(self):
        """
        Test the invitation procedure for one single member at a time.

        Load this member from the DB,
        assure the flag and token are not set,
        prepare cookies, invite this member,
        assure the flag and token are now set,
        """
        # pylint: disable=too-many-statements
        member1 = C3sMember.get_by_id(1)
        invitation = GeneralAssemblyRepository.get_member_invitation(
            member1.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertEqual(invitation['flag'], False)
        self.assertTrue(invitation['token'] is None)

        req = testing.DummyRequest()
        req.cookies['on_page'] = 0
        req.cookies['order'] = 'asc'
        req.cookies['orderby'] = 'id'

        # working membership number
        req.referer = '/members/'
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {
            'general_assembly': general_assembly,
            'member': member1,
        }

        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 0)

        self.config.registry.general_assembly_invitation.date \
            .today.side_effect = [date(2018, 1, 1)]
        res = general_assembly_invitation(req)

        self.assertEquals(res.status_code, 302)
        self.assertTrue('/members/' in res.location)

        invitation = GeneralAssemblyRepository.get_member_invitation(
            member1.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertEqual(invitation['flag'], True)
        self.assertTrue(invitation['token'] is not None)
        self.assertEqual(len(mailer.outbox), 1)

        # test other redirect for referer different from '/members/'
        member3 = C3sMember.get_by_id(3)
        req.referer = 'something_else'
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {
            'general_assembly': general_assembly,
            'member': member3,
        }

        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 1)

        self.config.registry.general_assembly_invitation.date \
            .today.side_effect = [date(2018, 1, 1)]
        res = general_assembly_invitation(req)

        self.assertEquals(res.status_code, 302)
        self.assertTrue('/memberships' in res.location)

        invitation = GeneralAssemblyRepository.get_member_invitation(
            member3.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertEqual(invitation['flag'], True)
        self.assertTrue(invitation['token'] is not None)
        self.assertEqual(len(mailer.outbox), 2)

        # Try to invite again which should not cause another email to be sent
        res = general_assembly_invitation(req)
        self.assertEqual(len(mailer.outbox), 2)

        invitation = GeneralAssemblyRepository.get_member_invitation(
            member1.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertTrue(u'Einladung' in mailer.outbox[0].subject)
        self.assertTrue(member1.firstname
                        in mailer.outbox[0].body)
        # Token not in email template for current general assembly of
        # 2018-12-01. Testing needs to be performed with dummy templates.
        # self.assertTrue(invitation['token']
        #                 in mailer.outbox[0].body)

        # send invitation to English member
        member2 = C3sMember.get_by_id(2)
        invitation = GeneralAssemblyRepository.get_member_invitation(
            member2.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertEqual(invitation['flag'], False)
        self.assertTrue(invitation['token'] is None)
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {
            'general_assembly': general_assembly,
            'member': member2,
        }

        self.config.registry.general_assembly_invitation.date \
            .today.side_effect = [date(2018, 1, 1)]
        res = general_assembly_invitation(req)
        invitation = GeneralAssemblyRepository.get_member_invitation(
            member2.membership_number, CURRENT_GENERAL_ASSEMBLY)
        self.assertEqual(invitation['flag'], True)
        self.assertTrue(invitation['token'] is not None)
        self.assertEqual(len(mailer.outbox), 3)
        self.assertTrue(u'Invitation' in mailer.outbox[2].subject)
        self.assertTrue(member2.firstname
                        in mailer.outbox[2].body)
        # Token not in email template for current general assembly of
        # 2018-12-01. Testing needs to be performed with dummy templates.
        # self.assertTrue(invitation['token']
        #                 in mailer.outbox[1].body)

    def test_invitation_batch(self):
        """
        Test the invitation procedure, batch mode.
        """
        members = C3sMember.get_all()
        for member in members:
            invitation = GeneralAssemblyRepository.get_member_invitation(
                member.membership_number, CURRENT_GENERAL_ASSEMBLY)
            self.assertEqual(invitation['flag'], False)
            self.assertTrue(invitation['token'] is None)
            self.assertTrue(member.membership_accepted is True)

        req = testing.DummyRequest()
        # have some cookies
        req.cookies['on_page'] = 0
        req.cookies['order'] = 'asc'
        req.cookies['orderby'] = 'id'

        # with matchdict
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_post = {'count': 1}
        req.validated_matchdict = {
            'general_assembly': general_assembly
        }

        invitees = GeneralAssemblyRepository.get_invitees(
            CURRENT_GENERAL_ASSEMBLY, 1000)
        self.assertEquals(len(invitees), 4)
        res = batch_invite(req)

        _messages = req.session.peek_flash('success')
        self.assertTrue(
            'sent out 1 mails (to members with membership numbers'
            in _messages[0])
        invitees = GeneralAssemblyRepository.get_invitees(
            CURRENT_GENERAL_ASSEMBLY, 1000)
        self.assertEquals(len(invitees), 3)

        # without matchdict
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {
            'general_assembly': general_assembly
        }
        req.validated_post = {'count': 5}
        res = batch_invite(req)
        invitees = GeneralAssemblyRepository.get_invitees(
            CURRENT_GENERAL_ASSEMBLY, 1000)
        self.assertEquals(len(invitees), 0)
        self.assertEqual(res.status_code, 302)
        _messages = req.session.peek_flash('success')
        self.assertTrue(
            'sent out 3 mails (to members with membership numbers'
            in _messages[1])
        # send more request with POST['number']
        req = testing.DummyRequest()
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {'general_assembly': general_assembly}
        req.validated_post = {'count': 5}
        res = batch_invite(req)

        req = testing.DummyRequest()
        general_assembly = mock.Mock()
        general_assembly.number = CURRENT_GENERAL_ASSEMBLY
        req.validated_matchdict = {'general_assembly': general_assembly}
        req.validated_post = {'count': 5}
        res = batch_invite(req)

        _messages = req.session.peek_flash('success')
        self.assertTrue(
            'no invitees left. all done!' in _messages)

        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 4)
