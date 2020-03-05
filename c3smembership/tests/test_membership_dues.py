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
        """
        Set up the MembershipDuesIntegration class for testing

        Create test records
        """
        super(MembershipDuesIntegration, cls).setUpClass()
        db_session = cls.get_db_session()

        cls.normal_de = C3sMember(
            firstname=u'Ada Musiziert',
            lastname=u'Traumhaft ÄÖÜ',
            email=u'normal_de@example.com',
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
            email=u'normal_en@example.com',
            address1=u'james addr 1',
            address2=u'james appartment 2',
            postcode=u'12345',
            city=u'Jamestown',
            country=u'Jamescountry',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_EN',
            password=u'jamesrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u'',
            num_shares=u'2',
        )
        db_session.add(cls.normal_en)

        cls.normal_fr = C3sMember(
            firstname=u'Jean',
            lastname=u'Bélanger',
            email=u'normal_fr@example.com',
            address1=u'jean addr 1',
            address2=u'jean appartment 2',
            postcode=u'12345',
            city=u'Jeantown',
            country=u'Jeancountry',
            locale=u'fr',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_FR',
            password=u'jeanrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u'',
            num_shares=u'3',
        )
        db_session.add(cls.normal_fr)

        cls.investing_de = C3sMember(
            firstname=u'Herman',
            lastname=u'Investorius',
            email=u'investing_de@example.com',
            address1=u'addr one4',
            address2=u'addr two4',
            postcode=u'12344',
            city=u'Footown M44',
            country=u'Foocountr4',
            locale=u'de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_DE',
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
            email=u'investing_en@example.com',
            address1=u'aone5',
            address2=u'atwo5',
            postcode=u'12355',
            city=u'Footown M45',
            country=u'Foocountr5',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_EN',
            password=u'arandompasswor5',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u'GEMA',
            num_shares=u'60',
        )
        db_session.add(cls.investing_en)

        cls.investing_es = C3sMember(
            firstname=u'José',
            lastname=u'Sanchez',
            email=u'investing_es@example.com',
            address1=u'aone5',
            address2=u'atwo5',
            postcode=u'12355',
            city=u'Footown M45',
            country=u'Foocountr5',
            locale=u'es',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_ES',
            password=u'joserandompasswor5',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        db_session.add(cls.investing_es)

        cls.legal_entity_de = C3sMember(
            firstname=u'Deutscher',
            lastname=u'Musikverlag',
            email=u'legal_entity_de@example.com',
            address1=u'foo bulevard',
            address2=u'123-345',
            postcode=u'98765',
            city=u'Foo',
            country=u'Bar',
            locale=u'de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'LEGAL_ENTITY_DE',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        cls.legal_entity_de.is_legalentity = True
        db_session.add(cls.legal_entity_de)

        cls.legal_entity_en = C3sMember(
            firstname=u'English',
            lastname=u'Company',
            email=u'legal_entity_en@example.com',
            address1=u'foo boulevard',
            address2=u'123-345',
            postcode=u'98765',
            city=u'Foo',
            country=u'Bar',
            locale=u'en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'LOGAL_ENTITY_EN',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        cls.legal_entity_en.is_legalentity = True
        db_session.add(cls.legal_entity_en)

        cls.legal_entity_cz = C3sMember(
            firstname=u'Czech',
            lastname=u'Company',
            email=u'legal_entity_cz@example.com',
            address1=u'foo boulevard',
            address2=u'123-345',
            postcode=u'98765',
            city=u'Foo',
            country=u'Bar',
            locale=u'cz',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code=u'LOGAL_ENTITY_CZ',
            password=u'czrandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u'',
            num_shares=u'60',
        )
        cls.legal_entity_cz.is_legalentity = True
        db_session.add(cls.legal_entity_cz)

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

        response = self._send_invoice(1234)

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
        # 1 Membership within the dues year
        # 1.1 Membership started before the end of the dues year

        # Success in case membership began before the beginning of the year
        self._mock_mailer()
        self._reset_member(self.normal_de, membership_date=date(2019, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues20_invoice)

        # Success in case membership began during the year
        self._mock_mailer()
        self._reset_member(self.normal_de, membership_date=date(2020, 3, 1))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues20_invoice)

        # Error in case membership started after the end of the dues year
        self._reset_member(self.normal_de, membership_date=date(2021, 1, 1))

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2020. Therefore, you cannot send an '
            'invoice for 2020')

        # Error in case membership has not started
        self._reset_member(self.normal_de,
                           membership_date=None,
                           membership_accepted=False)

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(response, 'warning', 'not accepted by the board')

        # 1.2 Membership ended after the beginning of the dues year

        # Success in case membership ended during the year
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(2020, 3, 1),
                           membership_accepted=True,
                           membership_loss_date=date(2020, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues20_invoice)

        # Success in case membership ended after the end of the year
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(2020, 3, 1),
                           membership_loss_date=date(2020, 7, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues20_invoice)

        # Error in case membership ended before the beginning of the year
        self._reset_member(self.normal_de,
                           membership_date=date(2015, 2, 3),
                           membership_loss_date=date(2019, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues20_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2020. Therefore, you cannot send an '
            'invoice for 2020')

        # 2 User must be logged in as staff
        # Success if user is logged in as staff
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(2020, 3, 1),
                           membership_loss_date=date(2020, 7, 31))

        response = self._send_invoice(self.normal_de.id)

        # Failure if user is not logged in
        self.log_out()
        response = self.testapp.get('/dues20_invoice/1', status=403)

    def test_send_invoice_email_bl(self):
        """
        Test business logic (bl) of dues calculation and email sending

        Business logic:

        - 1 Due calculation for normal members

          - 1.1 Calculate quarterly dues
          - 1.2 Store dues data
          - 1.3 Store invoice data
          - 1.4 Generate invoice PDF

        - 2 No dues calculation for investing members
        - 3 Send email depending on membership type and entity type

          - 3.1 Normal members get email with invoice link
          - 3.2 Investing members get email

            - 3.2.1 For legal entities with request for amount based on
              turnover
            - 3.2.2 For natural persons with request for normal amount

          - 3.3 Send emails in German if member language is German
          - 3.4 Send email in English for other member languages than German
          - 3.5 Email is sent to member's email address

        - 4 Store that and when dues were calculated and email was sent

          - 4.1 For normal members
          - 4.2 For investing members

        - 5 If called again only resend email but only calculate dues once
        """
        self.log_in()
        db_session = self.get_db_session()

        # 1 Store that dues email was sent and when it was sent all members
        # 1.1 For normal members
        self._mock_mailer()
        self._reset_member(self.normal_de)

        self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues20_invoice)
        self.assertEqual(self.normal_de.dues20_invoice_date.date(),
                         date.today())

        # 1.2 For investing members
        self._mock_mailer()
        self._reset_member(self.investing_de)

        self._send_invoice(self.investing_de.id)

        self.assertTrue(self.investing_de.dues20_invoice)
        self.assertEqual(self.investing_de.dues20_invoice_date.date(),
                         date.today())

        # 1 Due calculation for normal members
        self._mock_mailer()
        self._reset_member(self.normal_de)

        self._send_invoice(self.normal_de.id)

        # 1.1 Calculate quarterly dues
        self.assertEqual(self.normal_de.dues20_amount, Decimal('50.0'))

        # 1.2 Store dues data
        self.assertTrue(self.normal_de.dues20_invoice)
        self.assertEqual(self.normal_de.dues20_invoice_date.date(),
                         date.today())
        self.assertIsNotNone(self.normal_de.dues20_invoice_no)
        self.assertIsNotNone(self.normal_de.dues20_token)
        self.assertEqual(self.normal_de.dues20_start, 'q1_2020')
        self.assertFalse(self.normal_de.dues20_reduced)
        self.assertTrue(self.normal_de.dues20_amount_reduced.is_nan())
        self.assertEqual(self.normal_de.dues20_balance, Decimal('50.0'))
        self.assertFalse(self.normal_de.dues20_balanced)
        self.assertFalse(self.normal_de.dues20_paid)
        self.assertEqual(self.normal_de.dues20_amount_paid, Decimal('0.0'))
        self.assertIsNone(self.normal_de.dues20_paid_date)

        # 1.3 Store invoice data
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

        # 1.4 Generate invoice PDF
        # TODO: Not yet implemented at this point but only when downloading or
        # archiving

        # 2 No dues calculation for investing members
        self._mock_mailer()
        self._reset_member(self.investing_de)

        self._send_invoice(self.investing_de.id)

        self.assertTrue(self.investing_de.dues20_invoice)
        self.assertEqual(self.investing_de.dues20_invoice_date.date(),
                         date.today())

        # 3 Send email depending on membership type and entity type
        # 3.1 Normal members get email with invoice link
        # English
        mailer = self._mock_mailer()
        self._reset_member(self.normal_en)

        self._send_invoice(self.normal_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertTrue('/dues20_invoice_no/{}/C3S-dues20-'.format(
            self.normal_en.dues20_token) in message.body)

        # German
        mailer = self._mock_mailer()
        self._reset_member(self.normal_de)

        self._send_invoice(self.normal_de.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue(
            'Die Rechnung findest Du unter folgendem Link:' in message.body)
        self.assertTrue('/dues20_invoice_no/{}/C3S-dues20-'.format(
            self.normal_de.dues20_token) in message.body)

        # French -> gets English email
        mailer = self._mock_mailer()
        self._reset_member(self.normal_fr)

        self._send_invoice(self.normal_fr.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertTrue('/dues20_invoice_no/{}/C3S-dues20-'.format(
            self.normal_fr.dues20_token) in message.body)

        # 3.2 Investing members get email
        # 3.2.1 For legal entities with request for amount based on turnover
        # English
        mailer = self._mock_mailer()
        self._reset_member(self.legal_entity_en)

        self._send_invoice(self.legal_entity_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('is an investing member' in message.body)

        # German
        mailer = self._mock_mailer()
        self._reset_member(self.legal_entity_de)

        self._send_invoice(self.legal_entity_de.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('investierendes Mitglied ist' in message.body)

        # Czech -> gets English email
        mailer = self._mock_mailer()
        self._reset_member(self.legal_entity_cz)

        self._send_invoice(self.legal_entity_cz.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('is an investing member' in message.body)

        # 3.2.2 For natural persons with request for normal amount
        # English
        mailer = self._mock_mailer()
        self._reset_member(self.investing_en)

        self._send_invoice(self.investing_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('Since you are an investing member' in message.body)

        # German
        mailer = self._mock_mailer()
        self._reset_member(self.investing_de)

        self._send_invoice(self.investing_de.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('Da Du investierendes Mitglied bist' in message.body)

        # Spanish -> gets English email
        mailer = self._mock_mailer()
        self._reset_member(self.investing_es)

        self._send_invoice(self.investing_es.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('Since you are an investing member' in message.body)

        # 3.3 Send emails in German if member language is German
        # Languages are tested with invoice sending

        # 3.4 Send email in English for other member languages than German
        # Languages are tested with invoice sending

        # 3.5 Email is sent to member's email address
        mailer = self._mock_mailer()
        self._reset_member(self.normal_en)

        self._send_invoice(self.normal_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertEqual(len(message.send_to), 1)
        self.assertTrue(self.normal_en.email in message.send_to)

        # 4 Store that and when dues were calculated and email was sent
        # 4.1 For normal members
        self._mock_mailer()
        self._reset_member(self.normal_en)
        self.assertFalse(self.normal_en.dues20_invoice)
        self.assertIsNone(self.normal_en.dues20_invoice_date)

        self._send_invoice(self.normal_en.id)

        self.assertTrue(self.normal_en.dues20_invoice)
        self.assertEqual(self.normal_en.dues20_invoice_date.date(),
                         date.today())

        # 4.2 For investing members
        self._mock_mailer()
        self._reset_member(self.investing_en)
        self.assertFalse(self.investing_en.dues20_invoice)
        self.assertIsNone(self.investing_en.dues20_invoice_date)

        self._send_invoice(self.investing_en.id)

        self.assertTrue(self.investing_en.dues20_invoice)
        self.assertEqual(self.investing_en.dues20_invoice_date.date(),
                         date.today())

        # 5 If called again only resend email but only calculate dues once
        mailer = self._mock_mailer()
        self._reset_member(self.normal_en, membership_date=date(2019, 12, 31))
        self._send_invoice(self.normal_en.id)
        self.assertEqual(self.normal_en.dues20_amount, Decimal('50.0'))
        self.assertEqual(self.normal_en.dues20_start, 'q1_2020')
        self.normal_en.membership_date = date(2020, 10, 1)
        self._mock_mailer()

        self._send_invoice(self.normal_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertEqual(self.normal_en.dues20_amount, Decimal('50.0'))
        self.assertEqual(self.normal_en.dues20_start, 'q1_2020')

    def _send_invoice(self, member_id):
        """
        Send the invoice by calling the TestApp URL
        """
        response = self.testapp.get('/dues20_invoice/{}'.format(member_id),
                                    headers={'Referer': 'test'},
                                    status=302)
        return response.follow()

    def _reset_member(self,
                      member,
                      membership_date=date(2020, 3, 1),
                      membership_accepted=True,
                      membership_loss_date=None):
        """
        Reset a member for a test case
        """
        member.membership_date = membership_date
        member.membership_accepted = membership_accepted
        member.membership_loss_date = membership_loss_date
        member.dues20_invoice = False
        member.dues20_invoice_date = None
        self.get_db_session().flush()

    def _mock_mailer(self):
        """
        Mock the mailer

        Let registry.get_mailer return a mock mailer
        """
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        return mailer

    @staticmethod
    def _get_mock_mailer_message(mailer):
        """
        Get the message from the mock mailer
        """
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]
        return message
