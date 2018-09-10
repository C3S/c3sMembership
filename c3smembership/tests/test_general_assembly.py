# -*- coding: utf-8 -*-

"""
Tests the invite_members package.
"""

from datetime import date
import unittest
from sqlalchemy import engine_from_config
from pyramid import testing
from pyramid_mailer import get_mailer
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.views.general_assembly import (
    batch_invite,
    invite_member_bcgv,
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
        # There is a side effect of test_initialization.py after which there are
        # still records in the database although it is setup from scratch.
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
        DBSession.add(member1)
        member2.membership_accepted = True
        DBSession.add(member2)
        member3.membership_accepted = True
        DBSession.add(member3)
        member4.membership_accepted = True
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
        self.config.add_route('membership_listing_backend', '/')
        self.config.add_route('toolbox', '/toolbox')
        self.config.add_route('dashboard', '/dashboard')
        self.config.registry.settings['c3smembership.url'] = 'http://foo.com'
        self.config.registry.settings['ticketing.url'] = 'http://bar.com'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'test@example.com'
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
        req.matchdict = {'m_id': 10000}
        res = invite_member_bcgv(req)
        self.assertEquals(302, res.status_code)

        req.matchdict = {'m_id': member1.id}
        res = invite_member_bcgv(req)

        self.assertEqual(member1.email_invite_flag_bcgv18, True)
        self.assertTrue(member1.email_invite_token_bcgv18 is not None)

        # send email
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        mailer = get_mailer(req)
        res = invite_member_bcgv(req)

        self.assertEqual(len(mailer.outbox), 2)
        self.assertTrue(u'[C3S] Einladung zu Barcamp und Generalversammlung'
                        in mailer.outbox[0].subject)
        self.assertTrue(u'[C3S] Einladung zu Barcamp und Generalversammlung'
                        in mailer.outbox[1].subject)
        self.assertTrue(member1.firstname
                        in mailer.outbox[1].body)
        self.assertTrue(member1.email_invite_token_bcgv18
                        in mailer.outbox[1].body)

        # send invitation to English member
        member2 = C3sMember.get_by_id(2)
        self.assertEqual(member2.email_invite_flag_bcgv18, False)
        self.assertTrue(member2.email_invite_token_bcgv18 is None)
        req.matchdict = {'m_id': member2.id}
        res = invite_member_bcgv(req)
        self.assertEqual(member2.email_invite_flag_bcgv18, True)
        self.assertTrue(member2.email_invite_token_bcgv18 is not None)
        self.assertEqual(len(mailer.outbox), 3)
        self.assertTrue(u'[C3S] Invitation to Barcamp and General Assembly'
                        in mailer.outbox[2].subject)
        self.assertTrue(member2.firstname
                        in mailer.outbox[2].body)
        self.assertTrue(member2.email_invite_token_bcgv18
                        in mailer.outbox[2].body)

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

        _messages = req.session.peek_flash('message_to_staff')
        # pylint: disable=superfluous-parens
        self.assertTrue(
            'sent out 1 mails (to members with ids [1])' in _messages)

        # without matchdict
        req.matchdict = {'number': ''}  # this triggers remaining 3
        res = batch_invite(req)
        self.assertEqual(res.status_code, 302)
        _messages = req.session.peek_flash('message_to_staff')

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

        _messages = req.session.peek_flash('message_to_staff')
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
