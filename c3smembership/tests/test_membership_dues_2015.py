# -*- coding: utf-8 -*-
"""
This module holds some Unit Tests for the 2015 Membership Dues functionality.

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

from pyramid import testing
from pyramid_mailer import get_mailer
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
from c3smembership.presentation.views.dues_2015 import (
    calculate_partial_dues15,
    dues15_listing,
    dues15_notice,
    dues15_reduction,
    make_dues15_invoice_no_pdf,
    make_dues15_reversal_invoice_pdf,
    make_random_string,
    send_dues15_invoice_batch,
    send_dues15_invoice_batch,
    send_dues15_invoice_email,
    send_dues15_invoice_email,
    string_start_quarter,
)


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
            firstname=u'Ada Musiziert',
            lastname=u'Traumhaft ÄÖÜ',
            email=u'devNull@example.com',
            address1=u"ada addr one",
            address2=u"ada addr two",
            postcode=u"12345",
            city=u"Foostadt Ada",
            country=u"Foocountry",
            locale=u"de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE1',
            password=u'adasrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'23',
        )
        normal_en = C3sMember(  # english normal
            firstname=u'James',
            lastname=u'Musician',
            email=u'dummy@example.com',
            address1=u"james addr 1",
            address2=u"james appartment 2",
            postcode=u"12345",
            city=u"Jamestown",
            country=u"Jamescountry",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE',
            password=u'jamesrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"",
            num_shares=u'2',
        )
        investing_de = C3sMember(  # german investing
            firstname=u'Herman',
            lastname=u'Investorius',
            email=u'dummy@example.com',
            address1=u"addr one4",
            address2=u"addr two4",
            postcode=u"12344",
            city=u"Footown M44",
            country=u"Foocountr4",
            locale=u"de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_DE',
            password=u'arandompasswor4',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'60',
        )
        investing_en = C3sMember(  # english investing
            firstname=u'Britany',
            lastname=u'Investing',
            email=u'dummy@example.com',
            address1=u"aone5",
            address2=u"atwo5",
            postcode=u"12355",
            city=u"Footown M45",
            country=u"Foocountr5",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_EN',
            password=u'arandompasswor5',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'60',
        )
        legal_entity_de = C3sMember(  # german investing legal entity
            firstname=u'Deutscher',
            lastname=u'Musikverlag',
            email=u'verlag@compa.ny',
            address1=u"foo bulevard",
            address2=u"123-345",
            postcode=u"98765",
            city=u"Foo",
            country=u"Bar",
            locale=u"de",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'VERLAG_DE',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'60',
        )
        legal_entity_en = C3sMember(  # english investing legal entity
            firstname=u'Francoise',
            lastname=u'Company',
            email=u'foo@compa.ny',
            address1=u"foo bulevard",
            address2=u"123-345",
            postcode=u"98765",
            city=u"Foo",
            country=u"Bar",
            locale=u"en",
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'COMPANY_EN',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'60',
        )
        DBSession.add(normal_de)
        DBSession.add(normal_en)
        DBSession.add(investing_de)
        DBSession.add(investing_en)
        legal_entity_de.is_legalentity = True
        DBSession.add(legal_entity_en)
        legal_entity_en.is_legalentity = True
        DBSession.add(legal_entity_de)

    return DBSession


class TestDues15Views(unittest.TestCase):
    """
    Basic tests for the views concerning membership dues (2015 edition)
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings[
            'c3smembership.url'] = 'https://yes.c3s.cc'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'c@example.com'
        self.config.registry.settings['testing.mail_to_console'] = 'false'
        self.session = _initTestingDB()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_random_string(self):
        res = make_random_string()
        self.assertEqual(len(res), 10)

    def test_calculate_partial_dues15(self):
        """
        A test to check if partial dues are calculated the right way.

        "Partial dues" means you have to pay for half a year only, for example.
        """
        member = C3sMember.get_by_id(1)
        res = calculate_partial_dues15(member)
        self.assertEqual(res, (u'q1_2015', D('50')))

        # english member
        member_en = C3sMember.get_by_id(2)
        res = calculate_partial_dues15(member_en)
        self.assertEqual(res, (u'q1_2015', D('50')))

        member_en.membership_date = date(2015, 6, 1)
        res = calculate_partial_dues15(member_en)
        self.assertEqual(res, (u'q2_2015', D('37.50')))

        member_en.membership_date = date(2015, 9, 1)
        res = calculate_partial_dues15(member_en)
        self.assertEqual(res, (u'q3_2015', D('25')))

        member_en.membership_date = date(2015, 11, 1)
        res = calculate_partial_dues15(member_en)
        self.assertEqual(res, (u'q4_2015', D('12.50')))

    def test_string_start_quarter(self):
        """
        Tests for the strings used for partial time spans.
        """
        member = C3sMember.get_by_id(1)

        member.dues15_start = 'q1_2015'
        res = string_start_quarter(member)
        self.assertTrue('Quartal 1' in res)
        member.dues15_start = 'q2_2015'
        res = string_start_quarter(member)
        self.assertTrue('Quartal 2' in res)
        member.dues15_start = 'q3_2015'
        res = string_start_quarter(member)
        self.assertTrue('Quartal 3' in res)
        member.dues15_start = 'q4_2015'
        res = string_start_quarter(member)
        self.assertTrue('Quartal 4' in res)

        member.locale = u'en'
        member.dues15_start = 'q1_2015'
        res = string_start_quarter(member)
        self.assertTrue('1st quarter' in res)
        member.dues15_start = 'q2_2015'
        res = string_start_quarter(member)
        self.assertTrue('2nd quarter' in res)
        member.dues15_start = 'q3_2015'
        res = string_start_quarter(member)
        self.assertTrue('3rd quarter' in res)
        member.dues15_start = 'q4_2015'
        res = string_start_quarter(member)
        self.assertTrue('4th quarter' in res)

    def test_send_dues15_invoice_email_single(self):
        """
        test the send_dues15_invoice_email view

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
        _number_of_invoices = len(DuesInvoiceRepository.get_all([2015]))

        self.config.add_route('toolbox', '/')
        self.config.add_route('detail', '/')
        self.config.add_route('make_dues15_invoice_no_pdf', '/')

        req = testing.DummyRequest()
        req.matchdict = {
            'member_id': '1',
        }
        req.referrer = 'detail'
        res = send_dues15_invoice_email(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue('http://example.com/' in res.headers['Location'])
        # member 1 not accepted by the board. problem!

        _number_of_invoices_2 = len(DuesInvoiceRepository.get_all([2015]))
        self.assertEqual(_number_of_invoices, 0)
        self.assertEqual(_number_of_invoices_2, 0)

        m1 = C3sMember.get_by_id(1)
        m1.membership_accepted = True

        res = send_dues15_invoice_email(req)

        _number_of_invoices_3 = len(DuesInvoiceRepository.get_all([2015]))
        self.assertEqual(_number_of_invoices_3, 1)

        # check for outgoing email
        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertTrue(
            'Verwendungszweck: C3S-dues2015-0001' in mailer.outbox[0].body)

        """
        now we try to get an id that does not exist
        """
        req2 = testing.DummyRequest()
        req2.matchdict = {
            'member_id': '1234',
        }
        req2.referrer = 'detail'
        res2 = send_dues15_invoice_email(req2)
        self.assertEqual(res2.status_code, 302)
        self.assertTrue('http://example.com/' in res2.headers['Location'])

        """
        what if we call that function (and send email) twice?
        test that no second invoice is created in DB.
        """
        req3 = testing.DummyRequest()
        req3.matchdict = {
            'member_id': '1',
        }
        req3.referrer = 'detail'
        res3 = send_dues15_invoice_email(req3)
        self.assertEqual(res3.status_code, 302)
        self.assertTrue('http://example.com/' in res3.headers['Location'])
        _number_of_invoices_4 = len(DuesInvoiceRepository.get_all([2015]))
        self.assertEqual(_number_of_invoices_3, _number_of_invoices_4)
        """
        check for email texts
        """
        self.assertEqual(len(mailer.outbox), 2)
        self.assertTrue(
            (u'Dein Mitgliedsbeitrag ab Quartal 1 beträgt also 50 Euro.')
            in mailer.outbox[0].body)
        self.assertTrue(
            (u'Dein Mitgliedsbeitrag ab Quartal 1 beträgt also 50 Euro.')
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
        req_en_normal.referrer = 'detail'
        res_en_normal = send_dues15_invoice_email(req_en_normal)
        self.assertEqual(res_en_normal.status_code, 302)
        self.assertEqual(len(mailer.outbox), 3)
        self.assertTrue(
            (u'Please transfer 50 Euro')
            in mailer.outbox[2].body)

        # german investing ###################################################
        m3 = C3sMember.get_by_id(3)
        m3.membership_accepted = True
        req_de_investing = testing.DummyRequest()
        req_de_investing.matchdict = {
            'member_id': '3',
        }
        req_de_investing.referrer = 'detail'
        res_de_investing = send_dues15_invoice_email(req_de_investing)
        self.assertEqual(res_de_investing.status_code, 302)
        self.assertEqual(len(mailer.outbox), 4)
        self.assertTrue(
            (u'Da Du investierendes Mitglied bist')
            in mailer.outbox[3].body)

        # english investing ##################################################
        m4 = C3sMember.get_by_id(4)
        m4.membership_accepted = True
        req_en_investing = testing.DummyRequest()
        req_en_investing.matchdict = {
            'member_id': '4',
        }
        req_en_investing.referrer = 'detail'
        res_en_investing = send_dues15_invoice_email(req_en_investing)
        self.assertEqual(res_en_investing.status_code, 302)
        self.assertEqual(len(mailer.outbox), 5)
        self.assertTrue(
            (u'Since you are an investing member')
            in mailer.outbox[4].body)

        # german legal entity ################################################
        m5 = C3sMember.get_by_id(5)
        m5.membership_accepted = True
        req_de_legalentity = testing.DummyRequest()
        req_de_legalentity.matchdict = {
            'member_id': '5',
        }
        req_de_legalentity.referrer = 'detail'
        res_de_legalentity = send_dues15_invoice_email(req_de_legalentity)
        self.assertEqual(res_de_legalentity.status_code, 302)
        self.assertEqual(len(mailer.outbox), 6)
        self.assertTrue(
            (u'')
            in mailer.outbox[5].body)

        # english legal entity ###############################################
        m6 = C3sMember.get_by_id(6)
        m6.membership_accepted = True
        req_en_legalentity = testing.DummyRequest()
        req_en_legalentity.matchdict = {
            'member_id': '6',
        }
        req_en_legalentity.referrer = 'detail'
        res_en_legalentity = send_dues15_invoice_email(req_en_legalentity)
        self.assertEqual(res_en_legalentity.status_code, 302)
        self.assertEqual(len(mailer.outbox), 7)
        self.assertTrue(
            (u'Da Musikverlag investierendes Mitglied ist')
            in mailer.outbox[6].body)
        self.assertTrue(
            (u'Für juristische Personen wird empfohlen')
            in mailer.outbox[6].body)

    def test_send_dues15_invoice_email_via_BATCH(self):
        """
        test the send_dues15_invoice_batch function
        for batch processing
        """
        self.config.add_route('make_dues15_invoice_no_pdf', '/')
        self.config.add_route('make_dues15_reversal_invoice_pdf', '/')
        self.config.add_route('detail', '/detail/')
        self.config.add_route('error', '/error')
        self.config.add_route('toolbox', '/toolbox')

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

        _number_of_invoices_before_batch = len(
            DuesInvoiceRepository.get_all([2015]))
        self.assertEqual(_number_of_invoices_before_batch, 0)

        req = testing.DummyRequest()
        req.referrer = 'toolbox'
        res = send_dues15_invoice_batch(req)

        _number_of_invoices_batch = len(DuesInvoiceRepository.get_all([2015]))
        self.assertEqual(_number_of_invoices_batch, 2)

        # try to post a number for batch processing
        req_post = testing.DummyRequest(
            post={
                'submit': True,
                'number': 24
            },
        )
        req.referrer = 'toolbox'
        res = send_dues15_invoice_batch(req_post)

        self.assertTrue(
            'sent out 5 mails (to members with ids [1, 2, 3, 4, 5])' in
            req.session.pop_flash('success'))

        # try to batch-send once more:
        # this will respond with a redirect and tell
        # that there are no invitees left
        res2 = send_dues15_invoice_batch(req)
        self.assertEquals(res2.status, '302 Found')
        self.assertEquals(res2.status_code, 302)
        self.assertTrue(
            'no invoicees left. all done!' in
            req.session.pop_flash('success'))

        """
        and now some tests for make_dues15_invoice_no_pdf
        """
        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token + 'false!!!',  # must fail
            'i': u'0001',
        }

        res = make_dues15_invoice_no_pdf(req2)

        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'i': u'1234',  # must fail
        }
        res = make_dues15_invoice_no_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        # wrong invoice token: must fail!
        i2 = DuesInvoiceRepository.get_by_number(2, 2015)
        i2.token = u'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues15_token,
            'i': u'3',  # must fail
        }
        res = make_dues15_invoice_no_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        #######################################################################
        # one more edge case:
        # check _inv.token must match code, or else!!!
        # first, set inv_code to something wrong:
        i1 = DuesInvoiceRepository.get_by_number(1, 2015)
        _old_i1_token = i1.token
        i1.token = u'not_right'
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'i': u'0001',
        }
        res = make_dues15_invoice_no_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])
        # reset it to what was there before
        i1.token = _old_i1_token
        #######################################################################
        # one more edge case:
        # check this invoice is not a reversal, or else no PDF!!!
        # first, set is_reversal to something wrong:
        i1 = DuesInvoiceRepository.get_by_number(1, 2015)
        _old_i1_reversal_status = i1.is_reversal  # False
        i1.is_reversal = True
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'i': u'0001',
        }
        res = make_dues15_invoice_no_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])
        # reset it to what was there before
        i1.is_reversal = _old_i1_reversal_status
        #######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'i': u'0001',
        }
        res = make_dues15_invoice_no_pdf(req2)
        self.assertTrue(PDF_SIZE_MIN < len(res.body) < PDF_SIZE_MAX)
        self.assertTrue('application/pdf' in res.headers['Content-Type'])

        """
        test dues listing
        """
        req_list = testing.DummyRequest()
        resp_list = dues15_listing(req_list)
        self.assertEqual(resp_list['count'], 2)

    def test_dues15_reduction(self):
        """
        test the dues15_reduction functionality
        """
        # have to accept their membersip first
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        m2 = C3sMember.get_by_id(2)  # english normal member
        m2.membership_accepted = True

        self.config.add_route('make_dues15_invoice_no_pdf', '/')
        self.config.add_route('make_dues15_reversal_invoice_pdf', '/')
        self.config.add_route('detail', '/detail/')
        self.config.add_route('error', '/error')
        self.config.add_route('toolbox', '/toolbox')
        req = testing.DummyRequest()
        req.referrer = 'toolbox'
        # send out invoices. this is a prerequisite for reductions
        res = send_dues15_invoice_batch(req)
        res
        """
        test reduction of dues
        """
        # pre-check
        self.assertFalse(m1.dues15_reduced)  # not reduced yet!
        _m1_amount_reduced = m1.dues15_amount_reduced  # is Decimal('0')
        _number_of_invoices_before_reduction = len(
            DuesInvoiceRepository.get_all([2015]))
        # we have 2 invoices as of now
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 2)
        # import the function under test

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

        res_reduce = dues15_reduction(req_reduce)  # call reduce on her

        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 2)

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

        res_reduce = dues15_reduction(req_reduce)  # call reduce on her

        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 2)

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
        res_reduce = dues15_reduction(req_reduce)
        # no new invoice
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 2)

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
        res_reduce = dues15_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(
            DuesInvoiceRepository.get_all([2015]))

        self.assertEqual(
            _number_of_invoices_before_reduction + 2,
            _number_of_invoices_after_reduction)
        self.assertEqual(_number_of_invoices_after_reduction, 4)
        self.assertTrue('detail' in res_reduce.headers['Location'])
        self.assertNotEqual(_m1_amount_reduced, m1.dues15_amount_reduced)
        self.assertEqual(m1.dues15_amount_reduced, 42)

        # check the invoice created
        _rev_inv = DuesInvoiceRepository.get_by_number(
            _number_of_invoices_before_reduction + 1, 2015)
        _new_inv = DuesInvoiceRepository.get_by_number(
            _number_of_invoices_before_reduction + 2, 2015)
        self.assertEqual(_rev_inv.invoice_amount, D('-50'))
        self.assertEqual(_new_inv.invoice_amount, D('42'))

        # we have 4 invoices as of now
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 4)

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
        res_reduce = dues15_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(
            DuesInvoiceRepository.get_all([2015]))

        # no new invoices were created, we still have 4 invoices
        self.assertEqual(len(DuesInvoiceRepository.get_all([2015])), 4)

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
        res_reduce = dues15_reduction(req_reduce)
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
        res_reduce = dues15_reduction(req_reduce)

        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 2
        res_reduce = dues15_reduction(req_reduce)
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
        res_reduce = dues15_reduction(req_reduce)
        m1.locale = u'en'
        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 1
        res_reduce = dues15_reduction(req_reduce)
        #############################################################
        """
        test reversal invoice PDF generation
        """

        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token + 'false!!!',  # must fail
            'no': u'0006',
        }
        res = make_dues15_reversal_invoice_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'no': u'1234',  # must fail
        }
        res = make_dues15_reversal_invoice_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        # wrong invoice token: must fail!
        i2 = DuesInvoiceRepository.get_by_number(2, 2015)
        i2.token = u'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues15_token,
            'no': u'2',  # must fail
        }
        res = make_dues15_reversal_invoice_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])

        ######################################################################
        # wrong invoice type (not a reversal): must fail! (edge case coverage)
        self.assertFalse(i2.is_reversal)
        i2.token = m2.dues15_token  # we give it a valid token
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues15_token,
            'no': u'0002',
        }
        res = make_dues15_reversal_invoice_pdf(req2)
        self.assertTrue('application/pdf' not in res.headers['Content-Type'])
        self.assertTrue('error' in res.headers['Location'])
        ######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues15_token,
            'no': u'0003',
        }
        res = make_dues15_reversal_invoice_pdf(req2)
        self.assertTrue(PDF_SIZE_MIN < len(res.body) < PDF_SIZE_MAX)
        self.assertTrue('application/pdf' in res.headers['Content-Type'])

    def test_dues15_notice(self):
        """
        test the dues15 notice view -- acknowledge incoming payments
        """
        self.config.add_route('detail', '/detail/')
        self.config.add_route('make_dues15_invoice_no_pdf', '/')
        # prepare test candidate
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        req0 = testing.DummyRequest(
            matchdict={'member_id': m1.id})
        req0.referrer = 'detail'
        resp0 = send_dues15_invoice_email(req0)
        resp0  # tame flymake

        partial_payment_amount = D('10')

        # here comes the request to test
        req1 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': partial_payment_amount,
                'payment_date': '2015-09-11',
            }
        )
        res1 = dues15_notice(req1)
        res1  # tame flymake

        # After the partial payment, some amount has been paid
        self.assertEqual(m1.dues15_paid, True)
        # it has been the partial payment amount
        self.assertEqual(m1.dues15_amount_paid, partial_payment_amount)
        self.assertEqual(m1.dues15_paid_date,
                         datetime(2015, 9, 11, 0, 0))
        # the balance is the original amount subtracted by the partial payment
        self.assertEqual(
            m1.dues15_balance, D(m1.dues15_amount) - partial_payment_amount)
        # and the account is not balanced.
        self.assertEqual(m1.dues15_balanced, False)

        # here comes the request to test
        req2 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': D(m1.dues15_amount) - partial_payment_amount,
                'payment_date': '2015-09-13',
            }
        )
        res2 = dues15_notice(req2)
        res2  # tame flymake

        # After the final payment, some amount has been paid
        self.assertEqual(m1.dues15_paid, True)
        # it has been the full amount
        self.assertEqual(m1.dues15_amount_paid, D('50'))
        self.assertEqual(m1.dues15_paid_date,
                         datetime(2015, 9, 13, 0, 0))
        # the balance is 0
        self.assertEqual(m1.dues15_balance, D('0'))
        # and the account is balanced.
        self.assertEqual(m1.dues15_balanced, True)
