# -*- coding: utf-8 -*-

from datetime import date
import unittest

from pyramid import testing
from pyramid_mailer import get_mailer
from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember


def _initTestingDB():
    my_settings = {
        'sqlalchemy.url': 'sqlite:///:memory:', }
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
            num_shares=u'23',
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
            num_shares=u'23',
        )
        DBSession.add(member1)
        DBSession.add(member2)

    return DBSession


class TestMailMailConfirmationViews(unittest.TestCase):
    """
    tests for the mail_mail_confirmation views
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings['c3smembership.url'] = 'http://foo.com'
        self.config.registry.settings['c3smembership.mailaddr'] = 'c@c3s.cc'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.config.registry.get_mailer = get_mailer
        DBSession.remove()
        self.session = _initTestingDB()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_mail_mail_confirmation_invalid_id(self):
        """
        test the mail_mail_confirmation view
        """
        from c3smembership.presentation.views.membership_acquisition import \
            mail_mail_conf
        self.config.add_route('join', '/')
        self.config.add_route('dashboard', '/dashboard/0/id/asc')
        request = testing.DummyRequest()
        request.matchdict = {'member_id': '10000'}  # invalid!
        request.cookies['on_page'] = 1
        request.cookies['order'] = 'asc'
        request.cookies['orderby'] = 'id'

        result = mail_mail_conf(request)

        self.assertTrue(result.status_code == 302)
        self.assertTrue(  # to dashboard
            'http://example.com/dashboard/0/id/asc' in result.location)

    def test_mail_mail_confirmation(self):
        """
        test the mail_mail_confirmation view
        """
        from c3smembership.presentation.views.membership_acquisition import \
            mail_mail_conf
        self.config.add_route('join', '/')
        self.config.add_route('dashboard', '/')
        from pyramid_mailer import get_mailer
        request = testing.DummyRequest()
        request.matchdict = {'member_id': '1'}
        request.cookies['on_page'] = 1
        request.cookies['order'] = 'asc'
        request.cookies['orderby'] = 'id'

        mailer = get_mailer(request)
        result = mail_mail_conf(request)

        self.assertTrue(result.status_code == 302)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject,
            u'C3S: E-Mail-Adresse bestätigen und Formular abrufen'
        )
        self.assertTrue(
            u'Hallo' in mailer.outbox[0].body)
        member = C3sMember.get_by_id(1)
        self.assertTrue(
            u'{} {}'.format(
                member.firstname, member.lastname) in mailer.outbox[0].body)
