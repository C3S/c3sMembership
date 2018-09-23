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
    general_assembly_invitation,
)


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

        DBSession.add(GeneralAssembly(
            1,
            u'1. ordentliche Generalversammlung',
            date(2014, 8, 23)))
        DBSession.add(GeneralAssembly(
            2,
            u'2. ordentliche Generalversammlung',
            date(2015, 6, 13)))
        DBSession.add(GeneralAssembly(
            3,
            u'3. ordentliche Generalversammlung',
            date(2016, 4, 17)))
        DBSession.add(GeneralAssembly(
            4,
            u'4. ordentliche Generalversammlung',
            date(2017, 4, 2)))
        DBSession.add(GeneralAssembly(
            5,
            u'5. ordentliche Generalversammlung',
            date(2018, 6, 3)))

        DBSession.flush()
    return DBSession


class TestInvitation(unittest.TestCase):
    """
    Tests the invitations.
    """

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.add_route('membership_listing_backend', '/')
        self.config.add_route('toolbox', '/toolbox')
        self.config.add_route('dashboard', '/dashboard')
        self.config.add_route('general_assembly', '/general_assembly')
        self.config.add_route('general_assemblies', '/general_assemblies')
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
        assure the email_invite_flag_bcgv18 and token are not set,
        prepare cookies, invite this member,
        assure the email_invite_flag_bcgv18 and token are now set,
        """
        member1 = C3sMember.get_by_id(1)
        self.assertEqual(member1.email_invite_flag_bcgv18, False)
        self.assertTrue(member1.email_invite_token_bcgv18 is None)

        req = testing.DummyRequest()
        # have some cookies
        req.cookies['on_page'] = 0
        req.cookies['order'] = 'asc'
        req.cookies['orderby'] = 'id'

        # try with non-existing id
        req.matchdict = {'membership_number': 10000}
        res = general_assembly_invitation(req)
        self.assertEquals(302, res.status_code)

        req.matchdict = {
            'number': '5',
            'membership_number': str(member1.membership_number),
        }

        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 0)

        self.config.registry.general_assembly_invitation.date \
            .today.side_effect = [date(2018, 1, 1)]
        res = general_assembly_invitation(req)

        self.assertEquals(res.status_code, 302)
        self.assertEqual(member1.email_invite_flag_bcgv18, True)
        self.assertTrue(member1.email_invite_token_bcgv18 is not None)
        self.assertEqual(len(mailer.outbox), 1)

        # Try to invite again which should not cause another email to be sent
        res = general_assembly_invitation(req)
        self.assertEqual(len(mailer.outbox), 1)

        self.assertTrue(u'[C3S] Einladung zu Barcamp und Generalversammlung'
                        in mailer.outbox[0].subject)
        self.assertTrue(member1.firstname
                        in mailer.outbox[0].body)
        self.assertTrue(member1.email_invite_token_bcgv18
                        in mailer.outbox[0].body)

        # send invitation to English member
        member2 = C3sMember.get_by_id(2)
        self.assertEqual(member2.email_invite_flag_bcgv18, False)
        self.assertTrue(member2.email_invite_token_bcgv18 is None)
        req.matchdict = {
            'number': '5',
            'membership_number': str(member2.membership_number),
        }

        self.config.registry.general_assembly_invitation.date \
            .today.side_effect = [date(2018, 1, 1)]
        res = general_assembly_invitation(req)
        self.assertEqual(member2.email_invite_flag_bcgv18, True)
        self.assertTrue(member2.email_invite_token_bcgv18 is not None)
        self.assertEqual(len(mailer.outbox), 2)
        self.assertTrue(u'[C3S] Invitation to Barcamp and General Assembly'
                        in mailer.outbox[1].subject)
        self.assertTrue(member2.firstname
                        in mailer.outbox[1].body)
        self.assertTrue(member2.email_invite_token_bcgv18
                        in mailer.outbox[1].body)

    def test_invitation_batch(self):
        """
        Test the invitation procedure, batch mode.
        """
        members = C3sMember.get_all()
        for member in members:
            self.assertEqual(member.email_invite_flag_bcgv18, False)
            self.assertTrue(member.email_invite_token_bcgv18 is None)
            self.assertTrue(member.membership_accepted is True)

        req = testing.DummyRequest()
        # have some cookies
        req.cookies['on_page'] = 0
        req.cookies['order'] = 'asc'
        req.cookies['orderby'] = 'id'

        # with matchdict
        req.matchdict = {'number': 1}  # this will trigger 1 invitation
        res = batch_invite(req)

        _messages = req.session.peek_flash('success')
        # pylint: disable=superfluous-parens
        self.assertTrue(
            'sent out 1 mails (to members with ids [1])' in _messages)

        # without matchdict
        req.matchdict = {'number': ''}  # this triggers remaining 3
        res = batch_invite(req)
        self.assertEqual(res.status_code, 302)
        _messages = req.session.peek_flash('success')

        self.assertTrue(
            'sent out 3 mails (to members with ids [2, 3, 4])' in _messages)
        # send more request with POST['number']
        req = testing.DummyRequest(
            POST={
                'number': 'foo',
                'submit': True,
            })
        res = batch_invite(req)

        req = testing.DummyRequest(
            POST={
                'number': 1,
                'submit': True,
            })
        res = batch_invite(req)

        _messages = req.session.peek_flash('success')
        self.assertTrue(
            'no invitees left. all done!' in _messages)

        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 4)

        # assumptions about those members and emails sent
        self.assertTrue('[C3S] Einladung' in mailer.outbox[0].subject)  # de
        self.assertTrue('[C3S] Invitation' in mailer.outbox[1].subject)  # en
        self.assertTrue('[C3S] Einladung' in mailer.outbox[2].subject)  # de
        self.assertTrue('[C3S] Invitation' in mailer.outbox[3].subject)  # en

        for member in members:
            # has been invited
            self.assertEqual(member.email_invite_flag_bcgv18, True)
            # has a token
            self.assertTrue(member.email_invite_token_bcgv18 is not None)
            # firstname and token are in email body
            self.assertTrue(
                members[member.id - 1].firstname in mailer.outbox[member.id - 1].body)
            self.assertTrue(
                members[member.id - 1].email_invite_token_bcgv18 in mailer.outbox[
                    member.id - 1].body)
