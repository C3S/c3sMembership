# -*- coding: utf-8 -*-
"""
Integration test the membership dues
"""

from datetime import date
from decimal import Decimal

from mock import Mock

from integration_test_base import IntegrationTestCaseBase

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues20invoice import Dues20Invoice


class MembershipDuesIntegration(IntegrationTestCaseBase):
    """
    Integration testing of the membership dues
    """
    @classmethod
    def setUpClass(cls):
        super(MembershipDuesIntegration, cls).setUpClass()
        db_session = cls.get_db_session()

        cls.normal_de = C3sMember(
            firstname=u'Ada Musiziert',
            lastname=u'Traumhaft ÄÖÜ',
            email=u'devNull@example.com',
            address1=u'ada addr one',
            address2=u'ada addr two',
            postcode=u'12345',
            city=u'Foostadt Ada',
            country=u'Foocountry',
            locale=u'de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE1',
            password=u'adasrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u'GEMA',
            num_shares=u'23',
        )
        db_session.add(cls.normal_de)

        cls.normal_en = C3sMember(
            firstname=u'James',
            lastname=u'Musician',
            email=u'dummy@example.com',
            address1=u'james addr 1',
            address2=u'james appartment 2',
            postcode=u'12345',
            city=u'Jamestown',
            country=u'Jamescountry',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE',
            password=u'jamesrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u'',
            num_shares=u'2',
        )
        db_session.add(cls.normal_en)

        cls.investing_de = C3sMember(
            firstname=u'Herman',
            lastname=u'Investorius',
            email=u'dummy@example.com',
            address1=u'addr one4',
            address2=u'addr two4',
            postcode=u'12344',
            city=u'Footown M44',
            country=u'Foocountr4',
            locale=u'de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'cls.INVESTING_DE',
            password=u'arandompasswor4',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u'GEMA',
            num_shares=u'60',
        )
        db_session.add(cls.investing_de)

        cls.investing_en = C3sMember(
            firstname=u'Britany',
            lastname=u'Investing',
            email=u'dummy@example.com',
            address1=u'aone5',
            address2=u'atwo5',
            postcode=u'12355',
            city=u'Footown M45',
            country=u'Foocountr5',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'cls.INVESTING_EN',
            password=u'arandompasswor5',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u'GEMA',
            num_shares=u'60',
        )
        db_session.add(cls.investing_en)

        cls.legal_entity_de = C3sMember(
            firstname=u'Deutscher',
            lastname=u'Musikverlag',
            email=u'verlag@compa.ny',
            address1=u'foo bulevard',
            address2=u'123-345',
            postcode=u'98765',
            city=u'Foo',
            country=u'Bar',
            locale=u'de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'VERLAG_DE',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        db_session.add(cls.legal_entity_de)

        cls.legal_entity_en = C3sMember(
            firstname=u'Francoise',
            lastname=u'Company',
            email=u'foo@compa.ny',
            address1=u'foo bulevard',
            address2=u'123-345',
            postcode=u'98765',
            city=u'Foo',
            country=u'Bar',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'COMPANY_EN',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        db_session.add(cls.legal_entity_en)

        db_session.flush()

    def test_send_invoice_email_iv(self):
        """
        Test input validation (iv) of dues calculation and email sending

        Input validation: Member must exist. The matchdict member_id must
        correspond to an existing member.
        """
        self.log_in()
        db_session = self.get_db_session()

        # 1 Input validation: error in case member does not exist
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1234',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(response, 'danger', 'Member ID 1234 does not exist')

    def test_send_invoice_email_bv(self):
        """
        Test business validation (bv) of dues calculation and email sending

        Business validation:

        - 1 Membership within the dues year

          - 1.1 Membership started before the end of the dues year
          - 1.2 Membership ended after the beginning of the dues year

        - 2 User must be logged in as staff
        """
        db_session = self.get_db_session()

        # 1 Membership within the dues year
        # 1.1 Membership started before the end of the dues year

        # Success in case membership began before the beginning of the year
        self._mock_mailer()
        self.normal_de.membership_date = date(2019, 12, 31)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = None
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.normal_de.dues20_invoice)

        # Success in case membership began during the year
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_number = '123'
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = None
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.normal_de.dues20_invoice)

        # Error in case membership started after the end of the dues year
        self.normal_de.membership_date = date(2021, 1, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2020. Therefore, you cannot send an invoice for 2020'
        )

        # 1.2 Membership ended after the beginning of the dues year

        # Success in case membership ended during the year
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = date(2020, 12, 31)
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.normal_de.dues20_invoice)

        # Success in case membership ended after the end of the year
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = date(2020, 7, 31)
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.normal_de.dues20_invoice)

        # Error in case membership ended before the beginning of the year
        self.normal_de.membership_date = date(2015, 2, 3)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = date(2019, 12, 31)
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2020. Therefore, you cannot send an invoice for 2020'
        )

        # 2 User must be logged in as staff
        # Success if user is logged in as staff
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = date(2020, 7, 31)
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)

        # Failure if user is not logged in
        self.log_out()
        response = self.testapp.get('/dues20_invoice/1', status=403)

    def test_send_invoice_email_bl(self):
        """
        Test business logic (bl) of dues calculation and email sending

        Business logic:

        - 1 Store that dues email was sent and when it was sent all members

          - 1.1 For normal members
          - 1.2 For investing members

        - 2 Due calculation for normal members

          - 2.1 Calculate quarterly dues
          - 2.2 Store dues data
          - 2.3 Store invoice data
          - 2.4 Generate invoice PDF

        - 3 No dues calculation for investing members
        - 4 Send email depending on membership type and entity type

          - 4.1 Normal members get email with invoice link
          - 4.2 Investing members get email

            - 4.2.1 For legal entities with request for amount based on
              turnover
            - 4.2.2 For natural persons with request for normal amount

          - 4.3 Send emails in German if member language is German
          - 4.4 Send email in English for other member languages than German
          - 4.5 Email is sent to member's email address
        """
        self.log_in()
        db_session = self.get_db_session()

        # 1 Store that dues email was sent and when it was sent all members
        # 1.1 For normal members
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = None
        self.normal_de.dues20_invoice = False
        self.normal_de.dues20_invoice_date = None
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.normal_de.dues20_invoice)
        self.assertEqual(self.normal_de.dues20_invoice_date.date(),
                         date.today())

        # 1.2 For investing members
        self._mock_mailer()
        self.investing_de.membership_date = date(2020, 3, 1)
        self.investing_de.membership_accepted = True
        self.investing_de.membership_loss_date = None
        self.investing_de.dues20_invoice = False
        self.investing_de.dues20_invoice_date = None
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/{}'.format(
            self.investing_de.id),
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.investing_de.dues20_invoice)
        self.assertEqual(self.investing_de.dues20_invoice_date.date(),
                         date.today())

        # 2 Due calculation for normal members
        self._mock_mailer()
        self.normal_de.membership_date = date(2020, 3, 1)
        self.normal_de.membership_accepted = True
        self.normal_de.membership_loss_date = None
        self.normal_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/1',
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        # 2.1 Calculate quarterly dues
        self.assertEqual(self.normal_de.dues20_amount, Decimal('50.0'))

        # 2.2 Store dues data
        self.assertTrue(self.normal_de.dues20_invoice)
        self.assertEqual(self.normal_de.dues20_invoice_date.date(),
                         date.today())
        self.assertIsNotNone(self.normal_de.dues20_invoice_no)
        self.assertIsNotNone(self.normal_de.dues20_token)
        self.assertEqual(self.normal_de.dues20_start, 'q1_2020')
        self.assertFalse(self.normal_de.dues20_reduced)
        self.assertTrue(self.normal_de.dues20_amount_reduced.is_nan())
        self.assertEquals(self.normal_de.dues20_balance, Decimal('50.0'))
        self.assertFalse(self.normal_de.dues20_balanced)
        self.assertFalse(self.normal_de.dues20_paid)
        self.assertEquals(self.normal_de.dues20_amount_paid, Decimal('0.0'))
        self.assertIsNone(self.normal_de.dues20_paid_date)

        # 2.3 Store invoice data
        invoice = db_session.query(Dues20Invoice).filter(
            Dues20Invoice.member_id == 1).first()
        self.assertIsNotNone(invoice.invoice_no)
        self.assertIsNotNone(invoice.invoice_no_string)
        self.assertEqual(invoice.invoice_date.date(), date.today())
        self.assertEqual(invoice.invoice_amount, Decimal('50.0'))
        self.assertFalse(invoice.is_cancelled)
        self.assertIsNone(invoice.cancelled_date)
        self.assertFalse(invoice.is_reversal)
        self.assertFalse(invoice.is_altered)
        self.assertEqual(invoice.membership_no,
                         self.normal_de.membership_number)
        self.assertEqual(invoice.email, self.normal_de.email)
        self.assertIsNotNone(invoice.token)
        self.assertIsNone(invoice.preceding_invoice_no)
        self.assertIsNone(invoice.succeeding_invoice_no)

        # 2.4 Generate invoice PDF
        # TODO: Not yet implemented at this point but only when downloading or
        # archiving

        # 3 No dues calculation for investing members
        self._mock_mailer()
        self.investing_de.membership_date = date(2020, 3, 1)
        self.investing_de.membership_accepted = True
        self.investing_de.membership_loss_date = None
        self.investing_de.dues20_invoice = False
        db_session.flush()

        response = self.testapp.get('/dues20_invoice/{}'.format(
            self.investing_de.id),
                                    headers={'Referer': 'test'},
                                    status=302)
        response = response.follow()

        self.assertTrue(self.investing_de.dues20_invoice)
        self.assertEqual(self.investing_de.dues20_invoice_date.date(),
                         date.today())
        # 3 Send email depending on membership type and entity type
        # 3.1 Normal members get email with invoice link
        # 3.2 Investing members get email
        # 3.2.1 For legal entities with request for amount based on turnover
        # 3.2.2 For natural persons with request for normal amount
        # 3.3 Send emails in German if member language is German
        # 3.4 Send email in English for other member languages than German
        # 3.5 Email is sent to member's email address

    def _mock_mailer(self):
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        return mailer

    def _get_mock_mailer_message(self, mailer):
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]
        return message
