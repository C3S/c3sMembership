# -*- coding: utf-8 -*-
"""
Integration test the c3smembership.presentation.views.membership_acquisition
package
"""

from datetime import (
    date,
    datetime,
    timedelta,
)

from mock import Mock
import pyramid_mailer

from integration_test_base import IntegrationTestCaseBase

from c3smembership.data.model.base.c3smember import C3sMember


class MembershipAcqIntegration(IntegrationTestCaseBase):
    """
    Integration testing of the membership_acquisition module
    """

    @classmethod
    def setUpClass(cls):
        super(MembershipAcqIntegration, cls).setUpClass()
        db_session = cls.get_db_session()
        cls.member = C3sMember(  # german
            firstname=u'SomeFirstnäme',
            lastname=u'SomeLastnäme',
            email=u'member@example.com',
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
            num_shares=23,
        )
        db_session.add(cls.member)
        db_session.flush()

    def test_switch_sig(self):
        """
        Test the switch_sig view

        Switch signature received flag of a member. If it is True set it to
        False, if False set it to True.

        1. If signature received flag is True then set it to False
        2. If signature received flag is False then set it to True
        3. Return to dashboard for dashboard referer
        4. Validation fails if the member does not have membership
        5. Validation fails if the member does not exist
        6. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. If signature received flag is True then set it to False
        self.member.signature_received = True
        response = self.testapp.get('/switch_sig/1', status=302)
        self.assertTrue('detail' in response.location)
        self.assertFalse(self.member.signature_received)

        # 2. If signature received flag is False then set it to True
        self.member.signature_received = False
        response = self.testapp.get('/switch_sig/1', status=302)
        self.assertTrue('detail' in response.location)
        self.assertTrue(self.member.signature_received)

        # 3. Return to dashboard for dashboard referer
        response = self.testapp.get(
            '/switch_sig/1', status=302, headers={'Referer': '/dashboard'})
        self.assertTrue('dashboard' in response.location)

        # 4. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/switch_sig/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 5. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/switch_sig/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 6. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/switch_sig/asdf')

    def test_switch_pay(self):
        """
        Test the switch_pay view

        Switch the payment received flag of a member. If it is True set it to
        False, if False set it to True.

        1. If payment received flag is True then set it to False
        2. If payment received flag is False then set it to True
        3. Return to dashboard for dashboard referer
        4. Validation fails if the member does not have membership
        5. Validation fails if the member does not exist
        6. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. If payment received flag is True then set it to False
        self.member.payment_received = True
        response = self.testapp.get('/switch_pay/1', status=302)
        self.assertTrue('detail' in response.location)
        self.assertFalse(self.member.payment_received)

        # 2. If payment received flag is False then set it to True
        self.member.payment_received = False
        response = self.testapp.get('/switch_pay/1', status=302)
        self.assertTrue('detail' in response.location)
        self.assertTrue(self.member.payment_received)

        # 3. Return to dashboard for dashboard referer
        response = self.testapp.get(
            '/switch_pay/1', status=302, headers={'Referer': '/dashboard'})
        self.assertTrue('dashboard' in response.location)

        # 4. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/switch_pay/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 5. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/switch_pay/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 6. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/switch_pay/asdf')

    def test_regenerate_pdf(self):
        """
        Test the regenerate_pdf view

        1. Generate PDF
        2. Validation fails if the code is not found
        3. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Generate PDF
        response = self.testapp.get(
            '/re_C3S_SCE_AFM_ABCDEFGFOO.pdf', status=200)
        self.assertTrue(100000 < len(response.body) < 500000)

        # 2. Validation fails if the code is not found
        self.assert_get_redirect_flash(
            '/re_C3S_SCE_AFM_abc123.pdf',
            '/dashboard',
            'danger',
            'A member with code abc123 does not exist')

        # 3. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/re_C3S_SCE_AFM_abc123.pdf')

    def test_mail_signature_conf(self):
        """
        Test the mail_signature_confirmation view

        1. Send email

           1. Return to dashboard
           2. An email is sent
           3. The email is sent from the setting's notification_sender email
              addess
           4. The email is sent to the member's email address
           5. The email contains a salutation with the member's first and last
              name
           6. The email contains the number of shares
           7. The email contains the value amount of the shares
           8. Sending the email is recorded with flag and timestamp

        2. Send mail with detail referer
        3. Validation fails if the member does not have membership
        4. Validation fails if the member does not exist
        5. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Send email
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        # TODO: Email mocking should be moved to IntegrationTestCaseBase to be
        # reusable
        self.assertFalse(self.member.signature_confirmed)
        self.assertTrue(
            self.member.signature_confirmed_date is None or
            self.member.signature_confirmed_date == datetime(1970, 1, 1))

        response = self.testapp.get(
            '/mail_sig_conf/1', status=302)

        # 1.1. Return to dashboard
        self.assertTrue('dashboard' in response.location)

        # 1.2. An email is sent
        response = response.follow()
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]
        # TODO: Email mocking should be moved to IntegrationTestCaseBase to be
        # reusable

        self.assertTrue(isinstance(message, pyramid_mailer.message.Message))
        # 1.3. The email is sent from the setting's notification_sender email
        #      addess

        self.assertEqual(
            message.sender,
            self.SETTINGS['c3smembership.notification_sender'])
        self.assertEqual(message.sender, 'membership@example.com')

        # 1.4. The email is sent to the member's email address
        self.assertEqual(len(message.recipients), 1)
        self.assertEqual(message.recipients[0], self.member.email)
        self.assertEqual(message.recipients[0], 'member@example.com')

        # 1.5. The email contains a salutation with the member's first and last
        # name
        self.assertTrue(
            u'{firstname} {lastname}'.format(
                firstname=self.member.firstname,
                lastname=self.member.lastname
            ) in message.body)
        self.assertTrue(u'SomeFirstnäme SomeLastnäme' in message.body)

        # 1.6. The email contains the number of shares
        self.assertTrue(
            u'{} share(s)'.format(self.member.num_shares) in message.body)
        self.assertTrue(u'23 share(s)' in message.body)

        # 1.7. The email contains the value amount of the shares
        self.assertTrue(
            u'{} Euro'.format(self.member.num_shares * 50) in message.body)
        self.assertTrue(u'1150 Euro' in message.body)

        # 1.8. Sending the email is recorded with flag and timestamp
        self.assertTrue(self.member.signature_confirmed)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.signature_confirmed_date
        self.assertTrue(delta < timedelta(minutes=1))

        # 2. Send mail with detail referer
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer

        response = self.testapp.get(
            '/mail_sig_conf/1', status=302, headers={'Referer': '/detail'})
        self.assertTrue('detail' in response.location)

        # 3. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/mail_sig_conf/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 4. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/mail_sig_conf/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 5. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/mail_sig_conf/1')

    def test_mail_pay_conf(self):
        """
        Test the mail_payment_confirmation view

        1. Send email

           1. Return to dashboard
           2. An email is sent
           3. The email is sent from the setting's notification_sender email
              addess
           4. The email is sent to the member's email address
           5. The email contains a salutation with the member's first and last
              name
           6. The email contains the number of shares
           7. The email contains the value amount of the shares
           8. Sending the email is recorded with flag and timestamp

        2. Send mail with detail referer
        3. Validation fails if the member does not have membership
        4. Validation fails if the member does not exist
        5. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Send email
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        self.assertFalse(self.member.payment_confirmed)
        self.assertTrue(
            self.member.payment_confirmed_date is None or
            self.member.payment_confirmed_date == datetime(1970, 1, 1))

        response = self.testapp.get(
            '/mail_pay_conf/1', status=302)

        # 1.1. Return to dashboard
        self.assertTrue('dashboard' in response.location)

        # 1.2. An email is sent
        response = response.follow()
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]

        self.assertTrue(isinstance(message, pyramid_mailer.message.Message))
        # 1.3. The email is sent from the setting's notification_sender email
        #      addess

        self.assertEqual(
            message.sender,
            self.SETTINGS['c3smembership.notification_sender'])
        self.assertEqual(message.sender, 'membership@example.com')

        # 1.4. The email is sent to the member's email address
        self.assertEqual(len(message.recipients), 1)
        self.assertEqual(message.recipients[0], self.member.email)
        self.assertEqual(message.recipients[0], 'member@example.com')

        # 1.5. The email contains a salutation with the member's first and last
        # name
        self.assertTrue(
            u'{firstname} {lastname}'.format(
                firstname=self.member.firstname,
                lastname=self.member.lastname
            ) in message.body)
        self.assertTrue(u'SomeFirstnäme SomeLastnäme' in message.body)

        # 1.6. The email contains the number of shares
        self.assertTrue(
            u'{} share(s)'.format(self.member.num_shares) in message.body)
        self.assertTrue(u'23 share(s)' in message.body)

        # 1.7. The email contains the value amount of the shares
        self.assertTrue(
            u'{} Euro'.format(self.member.num_shares * 50) in message.body)
        self.assertTrue(u'1150 Euro' in message.body)

        # 1.8. Sending the email is recorded with flag and timestamp
        self.assertTrue(self.member.payment_confirmed)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.payment_confirmed_date
        self.assertTrue(delta < timedelta(minutes=1))

        # 2. Send mail with detail referer
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer

        response = self.testapp.get(
            '/mail_pay_conf/1', status=302, headers={'Referer': '/detail'})
        self.assertTrue('detail' in response.location)

        # 3. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/mail_pay_conf/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 4. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/mail_pay_conf/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 5. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/mail_pay_conf/1')

    def test_mail_signature_reminder(self):
        """
        Test the mail_signature_reminder view

        1. Send first reminder email

           1. Return to dashboard
           2. An email is sent
           3. The email is sent from the setting's notification_sender email
              addess
           4. The email is sent to the member's email address
           5. The email contains a salutation with the member's first and last
              name
           6. Sending the email is recorded with counter and timestamp

        2. Send second mail with detail referer

           1. Return to detail page
           2. Counter is increased and timestamp is updated

        3. Validation fails if the member does not have membership
        4. Validation fails if the member does not exist
        5. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Send first reminder email
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        self.assertTrue(
            self.member.sent_signature_reminder is None or
            self.member.sent_signature_reminder == 0)
        self.assertTrue(
            self.member.sent_signature_reminder_date is None or
            self.member.sent_signature_reminder_date == datetime(1970, 1, 1))

        response = self.testapp.get(
            '/mail_sig_reminder/1', status=302)

        # 1.1. Return to dashboard
        self.assertTrue('dashboard' in response.location)

        # 1.2. An email is sent
        response = response.follow()
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]

        self.assertTrue(isinstance(message, pyramid_mailer.message.Message))
        # 1.3. The email is sent from the setting's notification_sender email
        #      addess

        self.assertEqual(
            message.sender,
            self.SETTINGS['c3smembership.notification_sender'])
        self.assertEqual(message.sender, 'membership@example.com')

        # 1.4. The email is sent to the member's email address
        self.assertEqual(len(message.recipients), 1)
        self.assertEqual(message.recipients[0], self.member.email)
        self.assertEqual(message.recipients[0], 'member@example.com')

        # 1.5. The email contains a salutation with the member's first and last
        # name
        self.assertTrue(
            u'{firstname} {lastname}'.format(
                firstname=self.member.firstname,
                lastname=self.member.lastname
            ) in message.body)
        self.assertTrue(u'SomeFirstnäme SomeLastnäme' in message.body)

        # 1.6. Sending the email is recorded with flag and timestamp
        self.assertEqual(self.member.sent_signature_reminder, 1)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.sent_signature_reminder_date
        self.assertTrue(delta < timedelta(minutes=1))

        # 2. Send second mail with detail referer
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        first_timestamp = self.member.sent_signature_reminder_date

        response = self.testapp.get(
            '/mail_sig_reminder/1', status=302, headers={'Referer': '/detail'})

        # 2.1. Return to detail page
        self.assertTrue('detail' in response.location)
        # 2.2. Counter is increased and timestamp is updated
        self.assertEqual(self.member.sent_signature_reminder, 2)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.sent_signature_reminder_date
        self.assertTrue(
            delta < timedelta(minutes=1) and
            self.member.sent_signature_reminder_date > first_timestamp)

        # 3. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/mail_sig_reminder/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 4. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/mail_sig_reminder/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 5. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/mail_sig_reminder/1')

    def test_mail_payment_reminder(self):
        """
        Test the mail_payment_reminder view

        1. Send first reminder email

           1. Return to dashboard
           2. An email is sent
           3. The email is sent from the setting's notification_sender email
              addess
           4. The email is sent to the member's email address
           5. The email contains a salutation with the member's first and last
              name
           6. Sending the email is recorded with counter and timestamp

        2. Send second mail with detail referer

           1. Return to detail page
           2. Counter is increased and timestamp is updated

        3. Validation fails if the member does not have membership
        4. Validation fails if the member does not exist
        5. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Send email
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        self.assertTrue(
            self.member.sent_payment_reminder is None or
            self.member.sent_payment_reminder == 0)
        self.assertTrue(
            self.member.sent_payment_reminder_date is None or
            self.member.sent_payment_reminder_date == datetime(1970, 1, 1))

        response = self.testapp.get(
            '/mail_pay_reminder/1', status=302)

        # 1.1. Return to dashboard
        self.assertTrue('dashboard' in response.location)

        # 1.2. An email is sent
        response = response.follow()
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]

        self.assertTrue(isinstance(message, pyramid_mailer.message.Message))
        # 1.3. The email is sent from the setting's notification_sender email
        #      addess

        self.assertEqual(
            message.sender,
            self.SETTINGS['c3smembership.notification_sender'])
        self.assertEqual(message.sender, 'membership@example.com')

        # 1.4. The email is sent to the member's email address
        self.assertEqual(len(message.recipients), 1)
        self.assertEqual(message.recipients[0], self.member.email)
        self.assertEqual(message.recipients[0], 'member@example.com')

        # 1.5. The email contains a salutation with the member's first and last
        # name
        self.assertTrue(
            u'{firstname} {lastname}'.format(
                firstname=self.member.firstname,
                lastname=self.member.lastname
            ) in message.body)
        self.assertTrue(u'SomeFirstnäme SomeLastnäme' in message.body)

        # 1.6. Sending the email is recorded with flag and timestamp
        self.assertEqual(self.member.sent_payment_reminder, 1)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.sent_payment_reminder_date
        self.assertTrue(delta < timedelta(minutes=1))

        # 2. Send second mail with detail referer
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer
        first_timestamp = self.member.sent_payment_reminder_date

        response = self.testapp.get(
            '/mail_pay_reminder/1', status=302, headers={'Referer': '/detail'})

        # 2.1. Return to detail page
        self.assertTrue('detail' in response.location)
        # 2.2. Counter is increased and timestamp is updated
        self.assertEqual(self.member.sent_payment_reminder, 2)
        # TODO: Use dependency injection for setting now() to
        # signature_confirmed and check it here
        delta = datetime.now() - self.member.sent_payment_reminder_date
        self.assertTrue(
            delta < timedelta(minutes=1) and
            self.member.sent_payment_reminder_date > first_timestamp)

        # 3. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/mail_pay_reminder/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 4. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/mail_pay_reminder/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 5. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/mail_pay_reminder/1')

    def test_mail_mail_conf(self):
        """
        Test the mail_mail_conf view

        1. Send email

           1. Return to dashboard
           2. An email is sent
           3. The email is sent from the setting's notification_sender email
              addess
           4. The email is sent to the member's email address
           5. The email contains a salutation with the member's first and last
              name
           6. The email contains a verification link with the email confirm
              code

        2. Validation fails if the member does not have membership
        3. Validation fails if the member does not exist
        4. Authorization as staff is required to access the view
        """
        self.log_in()

        # 1. Send email
        mailer = Mock()
        get_mailer = Mock()
        get_mailer.side_effect = [mailer]
        self.app.registry.get_mailer = get_mailer

        response = self.testapp.get(
            '/mail_mail_conf/1', status=302)

        # 1.1. Return to dashboard
        self.assertTrue('dashboard' in response.location)

        # 1.2. An email is sent
        response = response.follow()
        call = mailer.send.call_args_list.pop()
        call_tuple = call[0]
        message = call_tuple[0]

        self.assertTrue(isinstance(message, pyramid_mailer.message.Message))

        # 1.3. The email is sent from the setting's notification_sender email
        #      addess
        self.assertEqual(
            message.sender,
            self.SETTINGS['c3smembership.notification_sender'])
        self.assertEqual(message.sender, 'membership@example.com')

        # 1.4. The email is sent to the member's email address
        self.assertEqual(len(message.recipients), 1)
        self.assertEqual(message.recipients[0], self.member.email)
        self.assertEqual(message.recipients[0], 'member@example.com')

        # 1.5. The email contains a salutation with the member's first and last
        # name
        self.assertTrue(
            u'{firstname} {lastname}'.format(
                firstname=self.member.firstname,
                lastname=self.member.lastname
            ) in message.body)
        self.assertTrue(u'SomeFirstnäme SomeLastnäme' in message.body)

        # 1.6. The email contains a verification link with the email confirm
        #      code
        self.assertTrue(self.member.email_confirm_code in message.body)
        self.assertTrue(u'ABCDEFGFOO' in message.body)
        self.assertTrue(
            u'{}/verify/'.format(self.SETTINGS['c3smembership.url'])
            in message.body)
        self.assertTrue(
            u'http://membership.example.com/verify/' in message.body)

        # 3. Validation fails if the member does not have membership
        self.assert_get_redirect_flash(
            '/mail_mail_conf/asdf',
            '/dashboard',
            'danger',
            '"asdf" is not a number')

        # 4. Validation fails if the member does not exist
        self.assert_get_redirect_flash(
            '/mail_mail_conf/123',
            '/dashboard',
            'danger',
            'Member ID 123 does not exist')

        # 5. Authorization as staff is required to access the view
        self.log_out()
        self.assert_get_unauthorized('/mail_mail_conf/1')
