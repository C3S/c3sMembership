# -*- coding: utf-8 -*-
"""
Integration test the membership dues
"""

from datetime import date
from decimal import Decimal

from mock import Mock

from .integration_test_base import IntegrationTestCaseBase

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.dues23invoice import Dues23Invoice

YEAR = 2023


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
            firstname='Ada Musiziert',
            lastname='Traumhaft ÄÖÜ',
            email='normal_de@example.com',
            address1='ada addr one',
            address2='ada addr two',
            postcode='12345',
            city='Foostadt Ada',
            country='Foocountry',
            locale='de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='NORMAL_DE1',
            password='adasrandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc='GEMA',
            num_shares='23',
        )
        db_session.add(cls.normal_de)

        cls.normal_en = C3sMember(
            firstname='James',
            lastname='Musician',
            email='normal_en@example.com',
            address1='james addr 1',
            address2='james appartment 2',
            postcode='12345',
            city='Jamestown',
            country='Jamescountry',
            locale='en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='NORMAL_EN',
            password='jamesrandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc='',
            num_shares='2',
        )
        db_session.add(cls.normal_en)

        cls.normal_fr = C3sMember(
            firstname='Jean',
            lastname='Bélanger',
            email='normal_fr@example.com',
            address1='jean addr 1',
            address2='jean appartment 2',
            postcode='12345',
            city='Jeantown',
            country='Jeancountry',
            locale='fr',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='NORMAL_FR',
            password='jeanrandompassword',
            date_of_submission=date.today(),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc='',
            num_shares='3',
        )
        db_session.add(cls.normal_fr)

        cls.investing_de = C3sMember(
            firstname='Herman',
            lastname='Investorius',
            email='investing_de@example.com',
            address1='addr one4',
            address2='addr two4',
            postcode='12344',
            city='Footown M44',
            country='Foocountr4',
            locale='de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='INVESTING_DE',
            password='arandompasswor4',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=True,
            name_of_colsoc='GEMA',
            num_shares='60',
        )
        db_session.add(cls.investing_de)

        cls.investing_en = C3sMember(
            firstname='Britany',
            lastname='Investing',
            email='investing_en@example.com',
            address1='aone5',
            address2='atwo5',
            postcode='12355',
            city='Footown M45',
            country='Foocountr5',
            locale='en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='INVESTING_EN',
            password='arandompasswor5',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=True,
            name_of_colsoc='GEMA',
            num_shares='60',
        )
        db_session.add(cls.investing_en)

        cls.investing_es = C3sMember(
            firstname='José',
            lastname='Sanchez',
            email='investing_es@example.com',
            address1='aone5',
            address2='atwo5',
            postcode='12355',
            city='Footown M45',
            country='Foocountr5',
            locale='es',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='INVESTING_ES',
            password='joserandompasswor5',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc='',
            num_shares='60',
        )
        db_session.add(cls.investing_es)

        cls.legal_entity_de = C3sMember(
            firstname='Deutscher',
            lastname='Musikverlag',
            email='legal_entity_de@example.com',
            address1='foo bulevard',
            address2='123-345',
            postcode='98765',
            city='Foo',
            country='Bar',
            locale='de',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='LEGAL_ENTITY_DE',
            password='arandompasswor6',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc='',
            num_shares='60',
        )
        cls.legal_entity_de.is_legalentity = True
        db_session.add(cls.legal_entity_de)

        cls.legal_entity_en = C3sMember(
            firstname='English',
            lastname='Company',
            email='legal_entity_en@example.com',
            address1='foo boulevard',
            address2='123-345',
            postcode='98765',
            city='Foo',
            country='Bar',
            locale='en',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='LOGAL_ENTITY_EN',
            password='arandompasswor6',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc='',
            num_shares='60',
        )
        cls.legal_entity_en.is_legalentity = True
        db_session.add(cls.legal_entity_en)

        cls.legal_entity_cz = C3sMember(
            firstname='Czech',
            lastname='Company',
            email='legal_entity_cz@example.com',
            address1='foo boulevard',
            address2='123-345',
            postcode='98765',
            city='Foo',
            country='Bar',
            locale='cz',
            date_of_birth=date.today(),
            email_is_confirmed=False,
            email_confirm_code='LOGAL_ENTITY_CZ',
            password='czrandompasswor6',
            date_of_submission=date.today(),
            membership_type='investing',
            member_of_colsoc=False,
            name_of_colsoc='',
            num_shares='60',
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
        self.normal_de.dues23_invoice = False
        db_session.flush()

        response = self._send_invoice(1234)

        self.assertFalse(self.normal_de.dues23_invoice)
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
        self._reset_member(self.normal_de, membership_date=date(YEAR-1, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues23_invoice)

        # Success in case membership began during the year
        self._mock_mailer()
        self._reset_member(self.normal_de, membership_date=date(YEAR, 3, 1))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues23_invoice)

        # Error in case membership started after the end of the dues year
        self._reset_member(self.normal_de, membership_date=date(YEAR+1, 1, 1))

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues23_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2023. Therefore, the member is not '
            'applicable for dues in 2023.')

        # Error in case membership has not started
        self._reset_member(self.normal_de,
                           membership_date=None,
                           membership_accepted=False)

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues23_invoice)
        self.assert_flash(response, 'warning', 'not accepted by the board')

        # 1.2 Membership ended after the beginning of the dues year

        # Success in case membership ended during the year
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(YEAR, 3, 1),
                           membership_accepted=True,
                           membership_loss_date=date(YEAR, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues23_invoice)

        # Success in case membership ended after the end of the year
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(YEAR, 3, 1),
                           membership_loss_date=date(YEAR, 7, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertTrue(self.normal_de.dues23_invoice)

        # Error in case membership ended before the beginning of the year
        self._reset_member(self.normal_de,
                           membership_date=date(YEAR-5, 2, 3),
                           membership_loss_date=date(YEAR-1, 12, 31))

        response = self._send_invoice(self.normal_de.id)

        self.assertFalse(self.normal_de.dues23_invoice)
        self.assert_flash(
            response, 'warning',
            'Member 1 was not a member in 2023. Therefore, the member is not '
            'applicable for dues in 2023.')

        # 2 User must be logged in as staff
        # Success if user is logged in as staff
        self._mock_mailer()
        self._reset_member(self.normal_de,
                           membership_date=date(YEAR, 3, 1),
                           membership_loss_date=date(YEAR, 7, 31))

        response = self._send_invoice(self.normal_de.id)

        # Failure if user is not logged in
        self.log_out()
        response = self.testapp.get('/dues23_invoice/1', status=403)

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

        self.assertTrue(self.normal_de.dues23_invoice)
        self.assertEqual(self.normal_de.dues23_invoice_date.date(),
                         date.today())

        # 1.2 For investing members
        self._mock_mailer()
        self._reset_member(self.investing_de)

        self._send_invoice(self.investing_de.id)

        self.assertTrue(self.investing_de.dues23_invoice)
        self.assertEqual(self.investing_de.dues23_invoice_date.date(),
                         date.today())

        # 1 Due calculation for normal members
        self._mock_mailer()
        self._reset_member(self.normal_de)

        self._send_invoice(self.normal_de.id)

        # 1.1 Calculate quarterly dues
        self.assertEqual(self.normal_de.dues23_amount, Decimal('50.0'))

        # 1.2 Store dues data
        self.assertTrue(self.normal_de.dues23_invoice)
        self.assertEqual(self.normal_de.dues23_invoice_date.date(),
                         date.today())
        self.assertIsNotNone(self.normal_de.dues23_invoice_no)
        self.assertIsNotNone(self.normal_de.dues23_token)
        self.assertEqual(self.normal_de.dues23_start, 'q1_2023')
        self.assertFalse(self.normal_de.dues23_reduced)
        self.assertTrue(self.normal_de.dues23_amount_reduced.is_nan())
        self.assertEqual(self.normal_de.dues23_balance, Decimal('50.0'))
        self.assertFalse(self.normal_de.dues23_balanced)
        self.assertFalse(self.normal_de.dues23_paid)
        self.assertEqual(self.normal_de.dues23_amount_paid, Decimal('0.0'))
        self.assertIsNone(self.normal_de.dues23_paid_date)

        # 1.3 Store invoice data
        invoice = db_session.query(Dues23Invoice).filter(
            Dues23Invoice.member_id == 1).first()
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

        self.assertTrue(self.investing_de.dues23_invoice)
        self.assertEqual(self.investing_de.dues23_invoice_date.date(),
                         date.today())

        # 3 Send email depending on membership type and entity type
        # 3.1 Normal members get email with invoice link
        # English
        mailer = self._mock_mailer()
        self._reset_member(self.normal_en)

        self._send_invoice(self.normal_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertTrue('/dues23_invoice_no/{}/C3S-dues23-'.format(
            self.normal_en.dues23_token) in message.body)

        # German
        mailer = self._mock_mailer()
        self._reset_member(self.normal_de)

        self._send_invoice(self.normal_de.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue(
            'Die Rechnung findest Du unter folgendem Link:' in message.body)
        self.assertTrue('/dues23_invoice_no/{}/C3S-dues23-'.format(
            self.normal_de.dues23_token) in message.body)

        # French -> gets English email
        mailer = self._mock_mailer()
        self._reset_member(self.normal_fr)

        self._send_invoice(self.normal_fr.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertTrue('/dues23_invoice_no/{}/C3S-dues23-'.format(
            self.normal_fr.dues23_token) in message.body)

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
        self.assertFalse(self.normal_en.dues23_invoice)
        self.assertIsNone(self.normal_en.dues23_invoice_date)

        self._send_invoice(self.normal_en.id)

        self.assertTrue(self.normal_en.dues23_invoice)
        self.assertEqual(self.normal_en.dues23_invoice_date.date(),
                         date.today())

        # 4.2 For investing members
        self._mock_mailer()
        self._reset_member(self.investing_en)
        self.assertFalse(self.investing_en.dues23_invoice)
        self.assertIsNone(self.investing_en.dues23_invoice_date)

        self._send_invoice(self.investing_en.id)

        self.assertTrue(self.investing_en.dues23_invoice)
        self.assertEqual(self.investing_en.dues23_invoice_date.date(),
                         date.today())

        # 5 If called again only resend email but only calculate dues once
        # Normal
        mailer = self._mock_mailer()
        self._reset_member(self.normal_en, membership_date=date(YEAR-1, 12, 31))
        self._send_invoice(self.normal_en.id)
        self.assertEqual(self.normal_en.dues23_amount, Decimal('50.0'))
        self.assertEqual(self.normal_en.dues23_start, 'q1_2023')
        self.normal_en.membership_date = date(YEAR, 10, 1)
        self._mock_mailer()

        self._send_invoice(self.normal_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('You will find the invoice here:' in message.body)
        self.assertEqual(self.normal_en.dues23_amount, Decimal('50.0'))
        self.assertEqual(self.normal_en.dues23_start, 'q1_2023')

        # Investing
        mailer = self._mock_mailer()
        self._reset_member(self.investing_en,
                           membership_date=date(YEAR-1, 12, 31))
        self._send_invoice(self.investing_en.id)
        self.assertTrue(self.investing_en.dues23_invoice)
        self._mock_mailer()

        self._send_invoice(self.investing_en.id)

        message = self._get_mock_mailer_message(mailer)
        self.assertTrue('Since you are an investing member' in message.body)
        self.assertTrue(self.investing_en.dues23_invoice)

    def _send_invoice(self, member_id):
        """
        Send the invoice by calling the TestApp URL
        """
        response = self.testapp.get('/dues23_invoice/{}'.format(member_id),
                                    headers={'Referer': 'test'},
                                    status=302)
        return response.follow()

    def _reset_member(self,
                      member,
                      membership_date=date(YEAR, 3, 1),
                      membership_accepted=True,
                      membership_loss_date=None):
        """
        Reset a member for a test case
        """
        member.membership_date = membership_date
        member.membership_accepted = membership_accepted
        member.membership_loss_date = membership_loss_date
        member.dues23_invoice = False
        member.dues23_invoice_date = None
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
