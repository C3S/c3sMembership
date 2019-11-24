# -*- coding: utf-8 -*-
"""
Test membership certificate
"""

from datetime import (
    date,
    datetime,
    timedelta,
)
import unittest

from mock import Mock
from pyramid import testing
from pyramid.httpexceptions import HTTPFound
from pyramid_beaker import session_factory_from_settings
from pyramid_mailer import get_mailer
from sqlalchemy import engine_from_config
import transaction
from webtest import TestApp

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember

from c3smembership.tests.utils import check_certificate_git_present

from c3smembership.presentation.view_processing import ErrorHandler
from c3smembership.presentation.views.membership_certificate import (
    send_certificate_email,
    generate_certificate,
    generate_certificate_staff,

# DEBUG = True
DEBUG = False

_min_PDF_size = 40000
_max_PDF_size = 120000
cert_git_condition, cert_git_reason = check_certificate_git_present()


def init_testing_db():
    """
    Initialize the database for testing
    """
    my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
    engine = engine_from_config(my_settings)
    DBSession.configure(bind=engine)
    db_session = DBSession()
    Base.metadata.create_all(engine)
    with transaction.manager:
        # German
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
            email_confirm_code=u'ABCDEFGFOO',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'23',
        )
        # English
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
            email_confirm_code=u'ABCDEFGBAR',
            password=u'arandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'2',
        )
        # English
        founding_member3 = C3sMember(
            firstname=u'BBBSomeFirstnäme',
            lastname=u'YYYSomeLastnäme',
            email=u'some3@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'ABCBARdungHH_',
            password=u'anotherrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'2',
        )
        db_session.add(member1)
        db_session.add(member2)
        db_session.add(founding_member3)

    return db_session


class TestErrorHandler(ErrorHandler):
    """
    Dummy error handler for testing purposes collecting calls
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        """
        Initialize the TestErrorHandler object
        """
        self.calls = []

    def __call__(self, request, schema, errors):
        """
        Record the call to self.calls and forward to membership_listing_backend
        """
        self.calls.append({
            'request': request,
            'schema': schema,
            'errors': errors,
        })
        return HTTPFound(request.route_url('membership_listing_backend'))


@unittest.skipIf(cert_git_condition, cert_git_reason)
class TestMembershipCertificateViews(unittest.TestCase):
    """
    tests for the membership certificate views
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.set_session_factory(session_factory_from_settings({}))
        self.config.include('pyramid_mailer.testing')
        self.config.include('pyramid_chameleon')
        self.config.include('c3smembership.presentation.view_processing')
        self.error_handler = TestErrorHandler()
        self.config.set_colander_error_handler(self.error_handler)
        DBSession.remove()
        self.db_session = init_testing_db()
        self.config.registry.settings['testing.mail_to_console'] = 'no'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'test@example.com'
        self.config.add_route('join', '/')
        self.config.add_route('detail', '/detail')
        self.config.add_route('dashboard', '/')
        self.config.add_route('certificate_pdf', '/')
        self.config.add_route(
            'certificate_pdf_staff', '/certificate_pdf_staff/{member_id}')
        self.config.add_route(
            'membership_listing_backend', '/membership_listing_backend')

        self.config.add_route(
            'certificate_mail', '/cert_mail/{member_id}')
        self.config.scan(
            'c3smembership.presentation.views.membership_certificate')
        self.testapp = TestApp(self.config.make_wsgi_app())

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_send_cert_email_int(self):
        """
        Integration test the send_certificate_email view on presentation level

        The tests include matchdict validation but not business oder database
        layer integration.

        1. Validation failure, no a number
        2. Validation failure, no member found
        3. Validation success, listing redirect
        4. Validation success, detail redirect
        """
        # Setup
        member = Mock()
        member_information = Mock()
        self.config.registry.member_information = member_information

        # 1. Validation failure, no a number
        result = self.testapp.get('/cert_mail/asdf')

        self.assertEqual(
            self.error_handler.calls.pop()['errors']['member_id'],
            '"asdf" is not a number')
        self.assertTrue('membership_listing_backend' in result.location)

        # 2. Validation failure, no member found
        member_information.get_member_by_id.side_effect = [None]

        result = self.testapp.get('/cert_mail/1')

        self.assertEqual(
            self.error_handler.calls.pop()['errors']['member_id'],
            'Member ID 1 does not exist.')
        self.assertTrue('membership_listing_backend' in result.location)

        # 3. Validation success, listing redirect
        member_information.get_member_by_id.side_effect = [member]

        result = self.testapp.get('/cert_mail/1')

        self.assertTrue('membership_listing_backend' in result.location)

        # 4. Validation success, detail redirect
        member_information.get_member_by_id.side_effect = [member]

        result = self.testapp.get(
            '/cert_mail/1',
            headers={'Referer': 'http://example.com/detail'})

        self.assertTrue('detail' in result.location)

    def test_send_certificate_email_de(self):
        """
        test the send_certificate_email view (german)
        """
        request = testing.DummyRequest()
        request.validated_matchdict = {'member': C3sMember.get_by_id(1)}

        mailer = get_mailer(request)
        member1 = C3sMember.get_by_id(1)

        member1.membership_accepted = True
        member1.membership_loss_date = None
        result = send_certificate_email(request)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(
            mailer.outbox[0].subject,
            u"C3S-Mitgliedsbescheinigung"
        )
        self.assertTrue(
            u"Hallo SomeFirstnäme SomeLastnäme," in mailer.outbox[0].body)
        self.assertTrue(
            u"Deine persönliche Mitgliederbescheinig" in mailer.outbox[0].body)

        member1.membership_accepted = True
        member1.membership_loss_date = date.today() + timedelta(days=1)
        result = send_certificate_email(request)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(len(mailer.outbox), 2)

    def test_send_certificate_email_en(self):
        """
        test the send_certificate_email view (english)
        """
        member2 = C3sMember.get_by_id(2)

        self.config.add_route('join', 'join')
        self.config.add_route('dashboard', 'dashboard')
        self.config.add_route('certificate_pdf', 'certificate_pdf')
        self.config.add_route(
            'membership_listing_backend', 'membership_listing_backend')
        request = testing.DummyRequest()
        request.validated_matchdict = {'member': member2}

        mailer = get_mailer(request)
        result = send_certificate_email(request)
        self.assertEqual(result.status_code, 302)
        self.assertTrue('membership_listing_backend' in result.location)
        self.assertEqual(len(mailer.outbox), 1)

        request.referer = 'dashboard'

        result = send_certificate_email(request)
        self.assertEqual(result.status_code, 302)

        self.assertEqual(len(mailer.outbox), 2)
        self.assertEqual(
            mailer.outbox[1].subject,
            u"C3S membership certificate"
        )
        self.assertTrue(
            u"Hello AAASomeFirstnäme XXXSomeLastnäme,"
            in mailer.outbox[1].body)
        self.assertTrue(
            u"your personal membership certificate" in mailer.outbox[1].body)

    def test_generate_certificate_en(self):
        """
        test the certificate download view (english)
        """
        member2 = C3sMember.get_by_id(2)
        request = testing.DummyRequest()
        request.validated_matchdict = {
            'member': member2,
            'token': 'hotzenplotz',
        }

        result = generate_certificate(request)

        # check: this is *not* found because the token is *invalid*
        self.assertEqual(result.status_code, 404)

        request.validated_matchdict = {
            'member': member2,
            'token': 'hotzenplotz123',
        }
        member2.certificate_token = u'hotzenplotz123'
        member2.certificate_email_date = datetime.now() - timedelta(weeks=1)
        member2.membership_accepted = True
        member2.membership_loss_date = date.today() + timedelta(days=1)
        result = generate_certificate(request)
        self.assertEqual(result.status_code, 200)

        member2.certificate_email_date = datetime.now() - timedelta(weeks=1)
        member2.membership_accepted = True
        member2.membership_loss_date = None
        result = generate_certificate(request)

        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

    def test_generate_certificate_de(self):
        """
        test the certificate download view (german)
        """
        member1 = C3sMember.get_by_id(1)
        request = testing.DummyRequest()
        request.validated_matchdict = {
            'member': member1,
            'token': 'hotzenplotz',
        }

        result = generate_certificate(request)

        self.assertEqual(result.status_code, 404)  # not found

        request.validated_matchdict = {
            'member': member1,
            'token': 'hotzenplotz123',
        }
        member = C3sMember.get_by_id(1)
        member.certificate_token = u'hotzenplotz123'
        member.membership_accepted = True

        result = generate_certificate(request)
        self.assertEqual(result.status_code, 404)  # not found

        # test: email/token is too old
        member.certificate_email_date = datetime.now(
        ) - timedelta(weeks=3)
        result = generate_certificate(request)
        self.assertEqual(result.status_code, 404)  # not found

        # need to get the date right!
        member.certificate_email_date = datetime.now(
        ) - timedelta(weeks=1)
        result = generate_certificate(request)

        self.assertEqual(result.status_code, 200)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

        # edge case: member has one share
        member.certificate_token = u'hotzenplotz123'
        member.num_shares = 1

        result = generate_certificate(request)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

        # edge case: member has one share
        member.certificate_token = u'hotzenplotz123'
        member.is_legalentity = True

        result = generate_certificate(request)

        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

    def test_generate_cert_founder(self):
        """
        test the certificate download view (german)
        """
        request = testing.DummyRequest()
        member = C3sMember.get_by_id(3)
        request.validated_matchdict = {
            'member': member,
            'token': 'hotzenplotz123',
        }
        member.certificate_token = u'hotzenplotz123'
        member.membership_accepted = True

        # need to get the date right!
        member.certificate_email_date = datetime.now(
        ) - timedelta(weeks=1)
        result = generate_certificate(request)

        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

        # edge case: member has one share
        member.certificate_token = u'hotzenplotz123'
        member.num_shares = 1

        result = generate_certificate(request)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

        # edge case: member has one share
        member.certificate_token = u'hotzenplotz123'
        member.is_legalentity = True

        result = generate_certificate(request)
        member.locale = u'de'
        result = generate_certificate(request)

        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

    def test_gen_cert_special_chars(self):
        """
        test the certificate generation with awkward characters in datasets
        because LaTeX interprets some characters as special characters.
        """
        member1 = C3sMember.get_by_id(1)
        request = testing.DummyRequest()
        request.validated_matchdict = {
            'member': member1,
            'token': 'hotzenplotz',
        }

        result = generate_certificate(request)

        self.assertEqual(result.status_code, 404)  # not found

        request.validated_matchdict = {
            'member': member1,
            'token': 'hotzenplotz123',
        }
        member = C3sMember.get_by_id(1)
        member.firstname = u"Foobar Corp & Co."
        member.lastname = u"Your Number #1"
        member.certificate_token = u'hotzenplotz123'
        member.membership_accepted = True

        # # need to get the date right!
        member.certificate_email_date = datetime.now(
        ) - timedelta(weeks=1)

        result = generate_certificate(request)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')

    def test_gen_cert_staff_int(self):
        """
        Integration test the generate_certificate_staff view

        1. Validation failure, no a number
        2. Validation failure, no member found
        3. Validation failure, membership not granted
        4. Validation success
        """
        member = Mock()
        member_information = Mock()
        self.config.registry.member_information = member_information

        # 1. Validation failure, no a number
        result = self.testapp.get('/certificate_pdf_staff/asdf')

        self.assertEqual(
            self.error_handler.calls.pop()['errors']['member_id'],
            '"asdf" is not a number')
        self.assertEqual(result.status_code, 302)
        self.assertTrue('membership_listing_backend' in result.location)

        # 2. Validation failure, no member found
        member_information.get_member_by_id.side_effect = [None]

        result = self.testapp.get('/certificate_pdf_staff/1')

        self.assertEqual(
            self.error_handler.calls.pop()['errors']['member_id'],
            'Member ID 1 does not exist.')
        self.assertEqual(result.status_code, 302)
        self.assertTrue('membership_listing_backend' in result.location)

        # 3. Validation failure, membership not granted
        member.is_member.side_effect = [False]
        member_information.get_member_by_id.side_effect = [member]

        result = self.testapp.get('/certificate_pdf_staff/1')

        self.assertEqual(
            self.error_handler.calls.pop()['errors']['member_id'],
            'Member with member ID 1 has not been granted membership')
        self.assertEqual(result.status_code, 302)
        self.assertTrue('membership_listing_backend' in result.location)

        # 4. Validation success
        member1 = C3sMember.get_by_id(1)
        member1.membership_accepted = True
        member_information.get_member_by_id.side_effect = [member1]

        result = self.testapp.get('/certificate_pdf_staff/1')

        self.assertEqual(result.status_code, 200)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)

    def test_generate_certificate_staff(self):
        """
        test the certificate generation option in the backend
        """
        request = testing.DummyRequest()
        request.validated_matchdict = {
            'member': C3sMember.get_by_id(1)
        }

        result = generate_certificate_staff(request)
        self.assertTrue(MIN_PDF_SIZE < len(result.body) < MAX_PDF_SIZE)
        self.assertEqual(result.content_type, 'application/pdf')
