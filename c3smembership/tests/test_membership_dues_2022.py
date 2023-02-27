# -*- coding: utf-8 -*-
"""
This module holds some Unit Tests for the Membership Dues functionality.

* send a single email
* send many emails (batch mode)
* reduce somebodies dues
* acknowledge incoming payments

A helper function named *_initTestingDB* is used to set up a database
for these tests: have some test data.

* normal members (english/german)
* investing members (english/german)
* legal entities (english/german)
"""

from datetime import (
    date,
    datetime)
from decimal import Decimal as D
# from pyramid.config import Configurator
from pyramid import testing
from sqlalchemy import engine_from_config
import transaction
import unittest

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository


PDF_SIZE_MIN = 20000
PDF_SIZE_MAX = 120000


def _initTestingDB():
    """
    Set up a database for these tests: have some test data.
    """
    my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
    engine = engine_from_config(my_settings)
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        normal_de = C3sMember(  # german normal
            firstname='Ada Musiziert',
            lastname='Traumhaft ÄÖÜ',
            email='devNull@example.com',
            address1="ada addr one",
            address2="ada addr two",
            postcode="12345",
            city="Foostadt Ada",
            country="Foocountry",
            locale="de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='NORMAL_DE1',
            password='adasrandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc="GEMA",
            num_shares='23',
        )
        normal_de.membership_number = 11
        normal_en = C3sMember(  # english normal
            firstname='James',
            lastname='Musician',
            email='dummy@example.com',
            address1="james addr 1",
            address2="james appartment 2",
            postcode="12345",
            city="Jamestown",
            country="Jamescountry",
            locale="en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='NORMAL_DE',
            password='jamesrandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc="",
            num_shares='2',
        )
        normal_en.membership_number = 12
        investing_de = C3sMember(  # german investing
            firstname='Herman',
            lastname='Investorius',
            email='dummy@example.com',
            address1="addr one4",
            address2="addr two4",
            postcode="12344",
            city="Footown M44",
            country="Foocountr4",
            locale="de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='INVESTING_DE',
            password='arandompasswor4',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=True,
            name_of_colsoc="GEMA",
            num_shares='60',
        )
        investing_de.membership_number = 13
        investing_en = C3sMember(  # english investing
            firstname='Britany',
            lastname='Investing',
            email='dummy@example.com',
            address1="aone5",
            address2="atwo5",
            postcode="12355",
            city="Footown M45",
            country="Foocountr5",
            locale="en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='INVESTING_EN',
            password='arandompasswor5',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=True,
            name_of_colsoc="GEMA",
            num_shares='60',
        )
        investing_en.membership_number = 14
        legal_entity_de = C3sMember(  # german investing legal entity
            firstname='Deutscher',
            lastname='Musikverlag',
            email='verlag@compa.ny',
            address1="foo bulevard",
            address2="123-345",
            postcode="98765",
            city="Foo",
            country="Bar",
            locale="de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='VERLAG_DE',
            password='arandompasswor6',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc="",
            num_shares='60',
        )
        legal_entity_de.membership_number = 15
        legal_entity_en = C3sMember(  # english investing legal entity
            firstname='Francoise',
            lastname='Company',
            email='foo@compa.ny',
            address1="foo bulevard",
            address2="123-345",
            postcode="98765",
            city="Foo",
            country="Bar",
            locale="en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='COMPANY_EN',
            password='arandompasswor6',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc="",
            num_shares='60',
        )
        legal_entity_en.membership_number = 16
        DBSession.add(normal_de)
        DBSession.add(normal_en)
        DBSession.add(investing_de)
        DBSession.add(investing_en)
        legal_entity_de.is_legalentity = True
        DBSession.add(legal_entity_en)
        legal_entity_en.is_legalentity = True
        DBSession.add(legal_entity_de)

    return DBSession


class TestDues22Views(unittest.TestCase):
    """
    Basic tests for the views concerning membership dues
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings[
            'c3smembership.url'] = 'https://yes.c3s.cc'
        self.config.registry.settings[
            'c3smembership.certificate_template'] = 'test'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'c@example.com'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.session = _initTestingDB()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_send_dues22_invoice_email_single(self):
        """
        test the send_dues22_invoice_email view

        * calculate invoice amount and send invoice email
        ** to not accepted member
        ** to accepted member
        ** to non-existing member (wrong id)
        ** to same member (just send email, don't create new invoice)

        ... and also check email texts for
        * german normal member
        * english normal member
        * german investing member
        * english investing member
        * german investing legal entity
        * english investing legal entity

        """
        from pyramid_mailer import get_mailer
        from c3smembership.presentation.views.dues_2022 import (
            send_dues22_invoice_email,
        )

        _number_of_invoices = len(DuesInvoiceRepository.get_all([2022]))

        self.config.add_route('dues', '/')
        self.config.add_route('detail', '/')
        self.config.add_route('membership_listing_backend', '/')
        self.config.add_route('make_dues22_invoice_no_pdf', '/')

        req = testing.DummyRequest()
        req.matchdict = {
            'member_id': '1',
        }
        req.referer = 'detail'
        req.validated_matchdict = {'member': C3sMember.get_by_id(1)}
        res = send_dues22_invoice_email(req)
        self.assertTrue(res.status_code == 302)
        self.assertTrue('http://example.com/' in res.headers['Location'])
        # member 1 not accepted by the board. problem!

        _number_of_invoices_2 = len(DuesInvoiceRepository.get_all([2022]))
        assert _number_of_invoices == _number_of_invoices_2 == 0

        m1 = C3sMember.get_by_id(1)
        m1.membership_accepted = True

        res = send_dues22_invoice_email(req)

        _number_of_invoices_3 = len(DuesInvoiceRepository.get_all([2022]))
        assert _number_of_invoices_3 == 1

        # check for outgoing email
        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertTrue(
            'Verwendungszweck: C3S-dues2022-0001' in mailer.outbox[0].body)

        """
        what if we call that function (and send email) twice?
        test that no second invoice is created in DB.
        """
        req3 = testing.DummyRequest()
        req3.matchdict = {
            'member_id': '1',
        }
        req3.referer = 'detail'
        req3.validated_matchdict = {'member': C3sMember.get_by_id(1)}
        res3 = send_dues22_invoice_email(req3)
        self.assertTrue(res3.status_code == 302)
        self.assertTrue('http://example.com/' in res3.headers['Location'])
        _number_of_invoices_4 = len(DuesInvoiceRepository.get_all([2022]))
        self.assertEqual(_number_of_invoices_3, _number_of_invoices_4)
        """
        check for email texts
        """
        self.assertEqual(len(mailer.outbox), 2)
        self.assertTrue(
            ('50 Euro. Er ist niedriger, falls du später als im 1. Quartal')
            in mailer.outbox[0].body)
        self.assertTrue(
            ('50 Euro. Er ist niedriger, falls du später als im 1. Quartal')
            in mailer.outbox[1].body)

        """
        send email to
        * english member,
        * investing members (de/en),
        * legal entities (de/en)
        """
        # english normal #####################################################
        m2 = C3sMember.get_by_id(2)
        m2.membership_accepted = True
        req_en_normal = testing.DummyRequest()
        req_en_normal.matchdict = {
            'member_id': '2',
        }
        req_en_normal.referer = 'detail'
        req_en_normal.validated_matchdict = {'member': C3sMember.get_by_id(2)}
        res_en_normal = send_dues22_invoice_email(req_en_normal)
        self.assertTrue(res_en_normal.status_code == 302)
        self.assertEqual(len(mailer.outbox), 3)
        self.assertTrue(
            ('Please transfer 50 Euro')
            in mailer.outbox[2].body)

        # german investing ###################################################
        m3 = C3sMember.get_by_id(3)
        m3.membership_accepted = True
        req_de_investing = testing.DummyRequest()
        req_de_investing.matchdict = {
            'member_id': '3',
        }
        req_de_investing.referer = 'detail'
        req_de_investing.validated_matchdict = {
            'member': C3sMember.get_by_id(3)}
        res_de_investing = send_dues22_invoice_email(req_de_investing)
        self.assertTrue(res_de_investing.status_code == 302)
        self.assertEqual(len(mailer.outbox), 4)
        self.assertTrue(
            ('Da Du investierendes Mitglied bist')
            in mailer.outbox[3].body)

        # english investing ##################################################
        m4 = C3sMember.get_by_id(4)
        m4.membership_accepted = True
        req_en_investing = testing.DummyRequest()
        req_en_investing.matchdict = {
            'member_id': '4',
        }
        req_en_investing.referer = 'detail'
        req_en_investing.validated_matchdict = {
            'member': C3sMember.get_by_id(4)}
        res_en_investing = send_dues22_invoice_email(req_en_investing)
        self.assertTrue(res_en_investing.status_code == 302)
        self.assertEqual(len(mailer.outbox), 5)
        self.assertTrue(
            ('Since you are an investing member')
            in mailer.outbox[4].body)

        # german legal entity ################################################
        m5 = C3sMember.get_by_id(5)
        m5.membership_accepted = True
        req_de_legalentity = testing.DummyRequest()
        req_de_legalentity.matchdict = {
            'member_id': '5',
        }
        req_de_legalentity.referer = 'detail'
        req_de_legalentity.validated_matchdict = {
            'member': C3sMember.get_by_id(5)}
        res_de_legalentity = send_dues22_invoice_email(req_de_legalentity)
        self.assertTrue(res_de_legalentity.status_code == 302)
        self.assertEqual(len(mailer.outbox), 6)
        self.assertTrue(
            ('')
            in mailer.outbox[5].body)

        # english legal entity ###############################################
        m6 = C3sMember.get_by_id(6)
        m6.membership_accepted = True
        req_en_legalentity = testing.DummyRequest()
        req_en_legalentity.matchdict = {
            'member_id': '6',
        }
        req_en_legalentity.referer = 'detail'
        req_en_legalentity.validated_matchdict = {
            'member': C3sMember.get_by_id(6)}
        res_en_legalentity = send_dues22_invoice_email(req_en_legalentity)
        self.assertTrue(res_en_legalentity.status_code == 302)
        self.assertEqual(len(mailer.outbox), 7)
        self.assertTrue(
            ('Da Musikverlag investierendes Mitglied ist')
            in mailer.outbox[6].body)
        self.assertTrue(
            ('Für juristische Personen wird empfohlen')
            in mailer.outbox[6].body)

    def test_send_dues22_invoice_email_via_BATCH(self):
        """
        test the send_dues22_invoice_batch function
        for batch processing
        """
        # from pyramid_mailer import get_mailer
        from c3smembership.presentation.views.dues_2022 import (
            send_dues22_invoice_batch,
        )
        self.config.add_route('make_dues22_invoice_no_pdf', '/')
        self.config.add_route('make_dues22_reversal_invoice_pdf', '/')
        self.config.add_route('detail', '/detail/')
        self.config.add_route('error', '/error')
        self.config.add_route('dues', '/dues')
        self.config.add_route('membership_listing_backend', '/')

        # have to accept their membersip first
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        m2 = C3sMember.get_by_id(2)  # english normal member
        m2.membership_accepted = True
        m3 = C3sMember.get_by_id(3)  # german investing member
        m3.membership_accepted = True
        m4 = C3sMember.get_by_id(4)  # english investing member
        m4.membership_accepted = True
        m5 = C3sMember.get_by_id(5)  # german investing member
        m5.membership_accepted = True
        m5 = C3sMember.get_by_id(6)  # english investing member
        m5.membership_accepted = True

        # check number of invoices: should be 0
        _number_of_invoices_before_batch = len(
            DuesInvoiceRepository.get_all([2022]))
        assert _number_of_invoices_before_batch == 0

        req = testing.DummyRequest()
        req.referer = 'toolbox'
        res = send_dues22_invoice_batch(req)

        # check number of invoices: should be 2
        _number_of_invoices_batch = len(DuesInvoiceRepository.get_all([2022]))
        assert _number_of_invoices_batch == 2

        # try to post a number for batch processing
        req_post = testing.DummyRequest(
            post={
                'submit': True,
                'number': 24
                # lots of values missing
            },
        )
        req_post.referer = 'toolbox'
        res = send_dues22_invoice_batch(req_post)

        self.assertTrue(
            'sent out 5 mails (to members with membership numbers [11, 12, '
            '13, 14, 16])' in
            req.session.pop_flash('success'))

        # try to batch-send once more:
        # this will respond with a redirect and tell
        # that there are no invitees left
        res2 = send_dues22_invoice_batch(req)
        self.assertEqual(res2.status, '302 Found')
        self.assertEqual(res2.status_code, 302)
        assert 'no invoicees left. all done!' \
               in req.session.pop_flash('success')

        """
        and now some tests for make_dues22_invoice_no_pdf
        """
        from c3smembership.presentation.views.dues_2022 import (
            make_dues22_invoice_no_pdf,
        )
        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token + 'false!!!',  # must fail
            'i': '0001',
        }

        res = make_dues22_invoice_no_pdf(req2)

        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'i': '1234',  # must fail
        }
        res = make_dues22_invoice_no_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        # wrong invoice token: must fail!
        i2 = DuesInvoiceRepository.get_by_number(2, 2022)
        i2.token = 'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues22_token,
            'i': '3',  # must fail
        }
        res = make_dues22_invoice_no_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        #######################################################################
        # one more edge case:
        # check _inv.token must match code, or else!!!
        # first, set inv_code to something wrong:
        i1 = DuesInvoiceRepository.get_by_number(1, 2022)
        _old_i1_token = i1.token
        i1.token = 'not_right'
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'i': '0001',
        }
        res = make_dues22_invoice_no_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error
        # reset it to what was there before
        i1.token = _old_i1_token
        #######################################################################
        # one more edge case:
        # check this invoice is not a reversal, or else no PDF!!!
        # first, set is_reversal to something wrong:
        i1 = DuesInvoiceRepository.get_by_number(1, 2022)
        _old_i1_reversal_status = i1.is_reversal  # False
        i1.is_reversal = True
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'i': '0001',
        }
        res = make_dues22_invoice_no_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error
        # reset it to what was there before
        i1.is_reversal = _old_i1_reversal_status
        #######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'i': '0001',
        }
        res = make_dues22_invoice_no_pdf(req2)
        self.assertTrue(PDF_SIZE_MIN < len(res.body) < PDF_SIZE_MAX)
        self.assertTrue('application/pdf' in res.headers['Content-Type'])

        """
        test dues listing
        """
        from c3smembership.presentation.views.dues_2022 import dues22_listing
        req_list = testing.DummyRequest()
        resp_list = dues22_listing(req_list)
        assert resp_list['count'] == 2

    def test_dues22_reduction(self):
        """
        test the dues22_reduction functionality
        """
        # have to accept their membersip first
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        m2 = C3sMember.get_by_id(2)  # english normal member
        m2.membership_accepted = True

        self.config.add_route('make_dues22_invoice_no_pdf', '/')
        self.config.add_route('make_dues22_reversal_invoice_pdf', '/')
        self.config.add_route('detail', '/detail/')
        self.config.add_route('error', '/error')
        self.config.add_route('dues', '/dues')
        req = testing.DummyRequest()
        req.referer = 'dues'
        from c3smembership.presentation.views.dues_2022 import (
            send_dues22_invoice_batch,
        )
        # send out invoices. this is a prerequisite for reductions
        res = send_dues22_invoice_batch(req)
        res
        """
        test reduction of dues
        """
        # pre-check
        self.assertFalse(m1.dues22_reduced)  # not reduced yet!
        _m1_amount_reduced = m1.dues22_amount_reduced  # is Decimal('0')
        _number_of_invoices_before_reduction = len(
            DuesInvoiceRepository.get_all([2022]))
        # we have 2 invoices as of now
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 2)
        # import the function under test
        from c3smembership.presentation.views.dues_2022 import dues22_reduction

        #############################################################
        # try to reduce to the given calculated amount (edge case coverage)
        # this will not work, produce no new invoices
        req_reduce = testing.DummyRequest(  # prepare request
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 50,
            },
        )
        req_reduce.matchdict['member_id'] = 1  # do it for member with id 1

        res_reduce = dues22_reduction(req_reduce)  # call reduce on her

        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 2)

        #############################################################
        # try to reduce above the given calculated amount
        # this will not work, produce no new invoices
        req_reduce = testing.DummyRequest(  # prepare request
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 500,
            },
        )
        req_reduce.matchdict['member_id'] = 1  # do it for member with id 1

        res_reduce = dues22_reduction(req_reduce)  # call reduce on her

        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 2)

        #############################################################
        # valid reduction but without confirmation
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'no',
                'submit': True,
                'amount': 42,
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)
        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 2)

        #############################################################
        # valid reduction
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 42,
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(
            DuesInvoiceRepository.get_all([2022]))

        # two new invoices must have been issued
        assert (_number_of_invoices_before_reduction + 2) \
               == _number_of_invoices_after_reduction
        assert _number_of_invoices_after_reduction == 4
        assert 'detail' in res_reduce.headers['Location']  # 302 to detail p.
        assert _m1_amount_reduced != m1.dues22_amount_reduced  # changed!
        assert m1.dues22_amount_reduced == 42  # changed to 42!

        # check the invoice created
        _rev_inv = DuesInvoiceRepository.get_by_number(
            _number_of_invoices_before_reduction + 1, 2022)
        _new_inv = DuesInvoiceRepository.get_by_number(
            _number_of_invoices_before_reduction + 2, 2022)
        assert _rev_inv.invoice_amount == D('-50')
        assert _new_inv.invoice_amount == D('42')

        # we have 4 invoices as of now
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 4)

        #############################################################
        # now try to raise above the previous reduction
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 50,
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(
            DuesInvoiceRepository.get_all([2022]))

        # no new invoices were created, we still have 4 invoices
        self.assertEqual(len(DuesInvoiceRepository.get_all([2022])), 4)

        #############################################################
        # try to reduce to the same amount again (edge case coverage)
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 42,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)
        #############################################################
        # try to reduce to zero (edge case coverage)
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)

        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 2
        res_reduce = dues22_reduction(req_reduce)
        #############################################################
        # try to reduce to zero with english member (edge case coverage)
        # how to do this if you already reduced to zero? reduce to more first!
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 1,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)
        m1.locale = 'en'
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues22_reduction(req_reduce)
        #############################################################
        """
        test reversal invoice PDF generation
        """

        from c3smembership.presentation.views.dues_2022 import (
            make_dues22_reversal_invoice_pdf,
        )
        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token + 'false!!!',  # must fail
            'no': '0006',
        }
        res = make_dues22_reversal_invoice_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'no': '1234',  # must fail
        }
        res = make_dues22_reversal_invoice_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        # wrong invoice token: must fail!
        i2 = DuesInvoiceRepository.get_by_number(2, 2022)
        i2.token = 'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues22_token,
            'no': '2',  # must fail
        }
        res = make_dues22_reversal_invoice_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error

        ######################################################################
        # wrong invoice type (not a reversal): must fail! (edge case coverage)
        assert not i2.is_reversal  # i2 is not a reversal
        i2.token = m2.dues22_token  # we give it a valid token
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues22_token,
            'no': '0002',
        }
        res = make_dues22_reversal_invoice_pdf(req2)
        assert 'application/pdf' not in res.headers['Content-Type']  # no PDF
        assert 'error' in res.headers['Location']  # but error
        ######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues22_token,
            'no': '0003',
        }
        res = make_dues22_reversal_invoice_pdf(req2)
        self.assertTrue(PDF_SIZE_MIN < len(res.body) < PDF_SIZE_MAX)
        self.assertTrue('application/pdf' in res.headers['Content-Type'])

    def test_dues22_notice(self):
        """
        test the dues22 notice view -- acknowledge incoming payments
        """
        self.config.add_route('detail', '/detail/')
        self.config.add_route('make_dues22_invoice_no_pdf', '/')
        # prepare test candidate
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        from c3smembership.presentation.views.dues_2022 import (
            send_dues22_invoice_email
        )
        req0 = testing.DummyRequest(
            matchdict={'member_id': m1.id})
        req0.referer = 'detail'
        req0.validated_matchdict = {'member': m1}
        send_dues22_invoice_email(req0)

        partial_payment_amount = D('10')

        # here comes the request to test
        req1 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': partial_payment_amount,
                'payment_date': '2022-09-11',
            }
        )
        from c3smembership.presentation.views.dues_2022 import dues22_notice
        res1 = dues22_notice(req1)
        res1  # tame flymake

        # After the partial payment, some amount has been paid
        self.assertEqual(m1.dues22_paid, True)
        # it has been the partial payment amount
        self.assertEqual(m1.dues22_amount_paid, partial_payment_amount)
        self.assertEqual(m1.dues22_paid_date,
                         datetime(2022, 9, 11, 0, 0))
        # the balance is the original amount subtracted by the partial payment
        self.assertEqual(
            m1.dues22_balance, D(m1.dues22_amount) - partial_payment_amount)
        # and the account is not balanced.
        self.assertEqual(m1.dues22_balanced, False)

        # here comes the request to test
        req2 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': D(m1.dues22_amount) - partial_payment_amount,
                'payment_date': '2022-09-13',
            }
        )
        res2 = dues22_notice(req2)
        res2  # tame flymake

        # After the final payment, some amount has been paid
        self.assertEqual(m1.dues22_paid, True)
        # it has been the full amount
        self.assertEqual(m1.dues22_amount_paid, D('50'))
        self.assertEqual(m1.dues22_paid_date,
                         datetime(2022, 9, 13, 0, 0))
        # the balance is 0
        self.assertEqual(m1.dues22_balance, D('0'))
        # and the account is balanced.
        self.assertEqual(m1.dues22_balanced, True)

        # Test no payment amount entered
        request = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': '',
                'payment_date': '2022-09-13',
            }
        )
        response = dues22_notice(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('detail' in response.location)
        self.assertTrue('#dues22' in response.location)
        self.assertTrue('Invalid amount to pay' in request.session.pop_flash(
            'dues22notice_message_to_staff')[0])

        # Test no payment date entered
        request = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': '12.34',
                'payment_date': '',
            }
        )
        response = dues22_notice(request)
        self.assertTrue('detail' in response.location)
        self.assertTrue('#dues22' in response.location)
        self.assertTrue(
            'Invalid date for payment' in request.session.pop_flash(
                'dues22notice_message_to_staff')[0])
