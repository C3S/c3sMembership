# -*- coding: utf-8 -*-
"""
This module holds some Unit Tests for the 2018 Membership Dues functionality.

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
from c3smembership.data.model.base.dues18invoice import Dues18Invoice


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


class TestDues18Views(unittest.TestCase):
    """
    Basic tests for the views concerning membership dues (2018 edition)
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        self.config.registry.settings[
            'c3smembership.url'] = 'https://yes.c3s.cc'
        self.config.registry.settings['c3smembership.notification_sender'] = \
            'c@example.com'
        self.config.registry.settings['testing.mail_to_console'] = 'false'

        DBSession.remove()
        self.session = _initTestingDB()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_random_string(self):
        from c3smembership.presentation.views.dues_2018 import \
            make_random_string
        res = make_random_string()
        assert len(res) == 10

    def test_calculate_partial_dues18(self):
        """
        A test to check if partial dues are calculated the right way.

        "Partial dues" means you have to pay for half a year only, for example.
        """
        from c3smembership.presentation.views.dues_2018 import (
            calculate_partial_dues18)
        member = C3sMember.get_by_id(1)
        res = calculate_partial_dues18(member)
        assert res == (u'q1_2018', D('50'))

        # english member
        member_en = C3sMember.get_by_id(2)
        res = calculate_partial_dues18(member_en)
        assert res == (u'q1_2018', D('50'))

        member_en.membership_date = date(2018, 6, 1)
        res = calculate_partial_dues18(member_en)
        assert res == (u'q2_2018', D('37.50'))

        member_en.membership_date = date(2018, 9, 1)
        res = calculate_partial_dues18(member_en)
        assert res == (u'q3_2018', D('25'))

        member_en.membership_date = date(2018, 11, 1)
        res = calculate_partial_dues18(member_en)
        assert res == (u'q4_2018', D('12.50'))

    def test_string_start_quarter_dues18(self):
        """
        Tests for the strings used for partial time spans.
        """
        from c3smembership.presentation.views.dues_2018 import (
            string_start_quarter_dues18,
        )
        member = C3sMember.get_by_id(1)

        member.dues18_start = 'q1_2018'
        res = string_start_quarter_dues18(member)
        assert(u'für das ganze Jahr' in res)
        member.dues18_start = 'q2_2018'
        res = string_start_quarter_dues18(member)
        assert('Quartal 2' in res)
        member.dues18_start = 'q3_2018'
        res = string_start_quarter_dues18(member)
        assert('Quartal 3' in res)
        member.dues18_start = 'q4_2018'
        res = string_start_quarter_dues18(member)
        assert('Quartal 4' in res)

        member.locale = u'en'
        member.dues18_start = 'q1_2018'
        res = string_start_quarter_dues18(member)
        assert('for the whole year' in res)
        member.dues18_start = 'q2_2018'
        res = string_start_quarter_dues18(member)
        assert('2nd quarter' in res)
        member.dues18_start = 'q3_2018'
        res = string_start_quarter_dues18(member)
        assert('3rd quarter' in res)
        member.dues18_start = 'q4_2018'
        res = string_start_quarter_dues18(member)
        assert('4th quarter' in res)

    def test_send_dues18_invoice_email_single(self):
        """
        test the send_dues18_invoice_email view

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
        from c3smembership.presentation.views.dues_2018 import (
            send_dues18_invoice_email,
        )

        _number_of_invoices = len(Dues18Invoice.get_all())

        self.config.add_route('toolbox', '/')
        self.config.add_route('detail', '/')
        self.config.add_route('make_dues18_invoice_no_pdf', '/')

        req = testing.DummyRequest()
        req.matchdict = {
            'member_id': '1',
        }
        req.referrer = 'detail'
        res = send_dues18_invoice_email(req)
        self.assertTrue(res.status_code == 302)
        self.assertTrue('http://example.com/' in res.headers['Location'])
        # member 1 not accepted by the board. problem!

        _number_of_invoices_2 = len(Dues18Invoice.get_all())
        assert(_number_of_invoices == _number_of_invoices_2 == 0)

        m1 = C3sMember.get_by_id(1)
        m1.membership_accepted = True

        res = send_dues18_invoice_email(req)

        _number_of_invoices_3 = len(Dues18Invoice.get_all())
        assert(_number_of_invoices_3 == 1)

        # check for outgoing email
        mailer = get_mailer(req)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertTrue(
            'Verwendungszweck: C3S-dues2018-0001' in mailer.outbox[0].body)

        """
        now we try to get an id that does not exist
        """
        req2 = testing.DummyRequest()
        req2.matchdict = {
            'member_id': '1234',
        }
        req2.referrer = 'detail'
        res2 = send_dues18_invoice_email(req2)
        self.assertTrue(res2.status_code == 302)
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
        res3 = send_dues18_invoice_email(req3)
        self.assertTrue(res3.status_code == 302)
        self.assertTrue('http://example.com/' in res3.headers['Location'])
        _number_of_invoices_4 = len(Dues18Invoice.get_all())
        self.assertEqual(_number_of_invoices_3, _number_of_invoices_4)
        """
        check for email texts
        """
        self.assertEqual(len(mailer.outbox), 2)
        self.assertTrue(
            (u'Dein Mitgliedsbeitrag für das ganze Jahr beträgt also 50 Euro.')
            in mailer.outbox[0].body)
        self.assertTrue(
            (u'Dein Mitgliedsbeitrag für das ganze Jahr beträgt also 50 Euro.')
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
        res_en_normal = send_dues18_invoice_email(req_en_normal)
        self.assertTrue(res_en_normal.status_code == 302)
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
        res_de_investing = send_dues18_invoice_email(req_de_investing)
        self.assertTrue(res_de_investing.status_code == 302)
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
        res_en_investing = send_dues18_invoice_email(req_en_investing)
        self.assertTrue(res_en_investing.status_code == 302)
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
        res_de_legalentity = send_dues18_invoice_email(req_de_legalentity)
        self.assertTrue(res_de_legalentity.status_code == 302)
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
        res_en_legalentity = send_dues18_invoice_email(req_en_legalentity)
        self.assertTrue(res_en_legalentity.status_code == 302)
        self.assertEqual(len(mailer.outbox), 7)
        self.assertTrue(
            (u'Da Musikverlag investierendes Mitglied ist')
            in mailer.outbox[6].body)
        self.assertTrue(
            (u'Für juristische Personen wird empfohlen')
            in mailer.outbox[6].body)

    def test_send_dues18_invoice_email_via_BATCH(self):
        """
        test the send_dues18_invoice_batch function
        for batch processing
        """
        # from pyramid_mailer import get_mailer
        from c3smembership.presentation.views.dues_2018 import (
            send_dues18_invoice_batch,
        )
        self.config.add_route('make_dues18_invoice_no_pdf', '/')
        self.config.add_route('make_dues18_reversal_invoice_pdf', '/')
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

        # check number of invoices: should be 0
        _number_of_invoices_before_batch = len(Dues18Invoice.get_all())
        assert(_number_of_invoices_before_batch == 0)

        req = testing.DummyRequest()
        req.referrer = 'toolbox'
        res = send_dues18_invoice_batch(req)

        # check number of invoices: should be 2
        _number_of_invoices_batch = len(Dues18Invoice.get_all())
        assert(_number_of_invoices_batch == 2)

        # try to post a number for batch processing
        req_post = testing.DummyRequest(
            post={
                'submit': True,
                'number': 24
                # lots of values missing
            },
        )
        req.referrer = 'toolbox'
        res = send_dues18_invoice_batch(req_post)

        assert(
            'sent out 5 mails (to members with ids [1, 2, 3, 4, 5])' in
            req.session.pop_flash('success'))

        # try to batch-send once more:
        # this will respond with a redirect and tell
        # that there are no invitees left
        res2 = send_dues18_invoice_batch(req)
        self.assertEquals(res2.status, '302 Found')
        self.assertEquals(res2.status_code, 302)
        assert(
            'no invoicees left. all done!' in
            req.session.pop_flash('success'))

        """
        and now some tests for make_dues18_invoice_no_pdf
        """
        from c3smembership.presentation.views.dues_2018 import (
            make_dues18_invoice_no_pdf,
        )
        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token + 'false!!!',  # must fail
            'i': u'0001',
        }

        res = make_dues18_invoice_no_pdf(req2)

        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'i': u'1234',  # must fail
        }
        res = make_dues18_invoice_no_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        # wrong invoice token: must fail!
        i2 = Dues18Invoice.get_by_invoice_no(2)
        i2.token = u'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues18_token,
            'i': u'3',  # must fail
        }
        res = make_dues18_invoice_no_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        #######################################################################
        # one more edge case:
        # check _inv.token must match code, or else!!!
        # first, set inv_code to something wrong:
        i1 = Dues18Invoice.get_by_invoice_no(1)
        _old_i1_token = i1.token
        i1.token = u'not_right'
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'i': u'0001',
        }
        res = make_dues18_invoice_no_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error
        # reset it to what was there before
        i1.token = _old_i1_token
        #######################################################################
        # one more edge case:
        # check this invoice is not a reversal, or else no PDF!!!
        # first, set is_reversal to something wrong:
        i1 = Dues18Invoice.get_by_invoice_no(1)
        _old_i1_reversal_status = i1.is_reversal  # False
        i1.is_reversal = True
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'i': u'0001',
        }
        res = make_dues18_invoice_no_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error
        # reset it to what was there before
        i1.is_reversal = _old_i1_reversal_status
        #######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'i': u'0001',
        }
        res = make_dues18_invoice_no_pdf(req2)
        # m1.
        assert(60000 < len(res.body) < 80000)
        assert('application/pdf' in res.headers['Content-Type'])

        """
        test dues listing
        """
        from c3smembership.presentation.views.dues_2018 import dues18_listing
        req_list = testing.DummyRequest()
        resp_list = dues18_listing(req_list)
        # {'count': 5,
        #   'invoices': [
        #       <c3smembership.models.Dues18Invoice object at 0x7f95df761a50>,
        #       <c3smembership.models.Dues18Invoice object at 0x7f95df761690>,
        #       <c3smembership.models.Dues18Invoice object at 0x7f95df818a50>,
        #       <c3smembership.models.Dues18Invoice object at 0x7f95df761c90>,
        #       <c3smembership.models.Dues18Invoice object at 0x7f95df761c10>],
        #   '_today': datetime.date(2018, 9, 1)}
        assert(resp_list['count'] == 2)

    def test_dues18_reduction(self):
        """
        test the dues18_reduction functionality
        """
        # have to accept their membersip first
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        m2 = C3sMember.get_by_id(2)  # english normal member
        m2.membership_accepted = True

        self.config.add_route('make_dues18_invoice_no_pdf', '/')
        self.config.add_route('make_dues18_reversal_invoice_pdf', '/')
        self.config.add_route('detail', '/detail/')
        self.config.add_route('error', '/error')
        self.config.add_route('toolbox', '/toolbox')
        req = testing.DummyRequest()
        req.referrer = 'toolbox'
        from c3smembership.presentation.views.dues_2018 import (
            send_dues18_invoice_batch,
        )
        # send out invoices. this is a prerequisite for reductions
        res = send_dues18_invoice_batch(req)
        res
        """
        test reduction of dues
        """
        # pre-check
        self.assertFalse(m1.dues18_reduced)  # not reduced yet!
        _m1_amount_reduced = m1.dues18_amount_reduced  # is Decimal('0')
        _number_of_invoices_before_reduction = len(Dues18Invoice.get_all())
        # we have 2 invoices as of now
        self.assertEqual(len(Dues18Invoice.get_all()), 2)
        # import the function under test
        from c3smembership.presentation.views.dues_2018 import dues18_reduction

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

        res_reduce = dues18_reduction(req_reduce)  # call reduce on her

        self.assertEqual(len(Dues18Invoice.get_all()), 2)  # no new invoice

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

        res_reduce = dues18_reduction(req_reduce)  # call reduce on her

        self.assertEqual(len(Dues18Invoice.get_all()), 2)  # no new invoice

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
        res_reduce = dues18_reduction(req_reduce)
        self.assertEqual(len(Dues18Invoice.get_all()), 2)  # no new invoice

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
        res_reduce = dues18_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(Dues18Invoice.get_all())

        assert(  # two new invoices must have been issued
            (_number_of_invoices_before_reduction + 2) ==
            _number_of_invoices_after_reduction)
        assert(_number_of_invoices_after_reduction == 4)
        assert('detail' in res_reduce.headers['Location'])  # 302 to detail p.
        assert(_m1_amount_reduced != m1.dues18_amount_reduced)  # changed!
        assert(m1.dues18_amount_reduced == 42)  # changed to 42!

        # check the invoice created
        _rev_inv = Dues18Invoice.get_by_invoice_no(
            _number_of_invoices_before_reduction + 1)
        _new_inv = Dues18Invoice.get_by_invoice_no(
            _number_of_invoices_before_reduction + 2)
        assert(_rev_inv.invoice_amount == D('-50'))
        assert(_new_inv.invoice_amount == D('42'))

        # we have 4 invoices as of now
        self.assertEqual(len(Dues18Invoice.get_all()), 4)

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
        res_reduce = dues18_reduction(req_reduce)

        _number_of_invoices_after_reduction = len(Dues18Invoice.get_all())

        # no new invoices were created, we still have 4 invoices
        self.assertEqual(len(Dues18Invoice.get_all()), 4)

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
        res_reduce = dues18_reduction(req_reduce)
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
        res_reduce = dues18_reduction(req_reduce)

        req_reduce = testing.DummyRequest(
            post={
                'confirmed': 'yes',
                'submit': True,
                'amount': 0,
                # lots of values missing
            },
        )
        req_reduce.matchdict['member_id'] = 2
        res_reduce = dues18_reduction(req_reduce)
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
        res_reduce = dues18_reduction(req_reduce)
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
        res_reduce = dues18_reduction(req_reduce)
        #############################################################
        """
        test reversal invoice PDF generation
        """

        from c3smembership.presentation.views.dues_2018 import (
            make_dues18_reversal_invoice_pdf,
        )
        req2 = testing.DummyRequest()

        # wrong token: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token + 'false!!!',  # must fail
            'no': u'0006',
        }
        res = make_dues18_reversal_invoice_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        # wrong invoice number: must fail!
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'no': u'1234',  # must fail
        }
        res = make_dues18_reversal_invoice_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        # wrong invoice token: must fail!
        i2 = Dues18Invoice.get_by_invoice_no('2')
        i2.token = u'not_matching'
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues18_token,
            'no': u'2',  # must fail
        }
        res = make_dues18_reversal_invoice_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error

        ######################################################################
        # wrong invoice type (not a reversal): must fail! (edge case coverage)
        assert(not i2.is_reversal)  # i2 is not a reversal
        i2.token = m2.dues18_token  # we give it a valid token
        req2.matchdict = {
            'email': m2.email,
            'code': m2.dues18_token,
            'no': u'0002',
        }
        res = make_dues18_reversal_invoice_pdf(req2)
        assert('application/pdf' not in res.headers['Content-Type'])  # no PDF
        assert('error' in res.headers['Location'])  # but error
        ######################################################################

        # retry with valid token:
        req2.matchdict = {
            'email': m1.email,
            'code': m1.dues18_token,
            'no': u'0003',
        }
        res = make_dues18_reversal_invoice_pdf(req2)
        assert(60000 < len(res.body) < 80000)
        assert('application/pdf' in res.headers['Content-Type'])

    def test_dues18_notice(self):
        """
        test the dues18 notice view -- acknowledge incoming payments
        """
        self.config.add_route('detail', '/detail/')
        self.config.add_route('make_dues18_invoice_no_pdf', '/')
        # prepare test candidate
        m1 = C3sMember.get_by_id(1)  # german normal member
        m1.membership_accepted = True
        from c3smembership.presentation.views.dues_2018 import (
            send_dues18_invoice_email
        )
        req0 = testing.DummyRequest(
            matchdict={'member_id': m1.id})
        req0.referrer = 'detail'
        resp0 = send_dues18_invoice_email(req0)
        resp0  # tame flymake

        partial_payment_amount = D('10')

        # here comes the request to test
        req1 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': partial_payment_amount,
                'payment_date': '2018-09-11',
            }
        )
        from c3smembership.presentation.views.dues_2018 import dues18_notice
        res1 = dues18_notice(req1)
        res1  # tame flymake

        # After the partial payment, some amount has been paid
        self.assertEqual(m1.dues18_paid, True)
        # it has been the partial payment amount
        self.assertEqual(m1.dues18_amount_paid, partial_payment_amount)
        self.assertEqual(m1.dues18_paid_date,
                         datetime(2018, 9, 11, 0, 0))
        # the balance is the original amount subtracted by the partial payment
        self.assertEqual(
            m1.dues18_balance, D(m1.dues18_amount) - partial_payment_amount)
        # and the account is not balanced.
        self.assertEqual(m1.dues18_balanced, False)

        # here comes the request to test
        req2 = testing.DummyRequest(
            matchdict={'member_id': 1},
            POST={
                'amount': D(m1.dues18_amount) - partial_payment_amount,
                'payment_date': '2018-09-13',
            }
        )
        res2 = dues18_notice(req2)
        res2  # tame flymake

        # After the final payment, some amount has been paid
        self.assertEqual(m1.dues18_paid, True)
        # it has been the full amount
        self.assertEqual(m1.dues18_amount_paid, D('50'))
        self.assertEqual(m1.dues18_paid_date,
                         datetime(2018, 9, 13, 0, 0))
        # the balance is 0
        self.assertEqual(m1.dues18_balance, D('0'))
        # and the account is balanced.
        self.assertEqual(m1.dues18_balanced, True)
