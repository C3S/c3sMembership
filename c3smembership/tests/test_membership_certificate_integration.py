# -*- coding: utf-8 -*-
"""
Integration test the c3smembership.presentation.views.membership_certificate
package
"""

from datetime import (
    date,
    datetime,
    timedelta,
)

from integration_test_base import IntegrationTestCaseBase

from c3smembership.data.model.base.c3smember import C3sMember


class MembershipCertificateInt(IntegrationTestCaseBase):
    """
    Integration testing of the membership_acquisition module
    """
    @classmethod
    def setUpClass(cls):
        super(MembershipCertificateInt, cls).setUpClass()
        db_session = cls.get_db_session()
        cls.member = C3sMember(
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

    def reset_member(self):
        """
        Reset the member's properties for membership and certificate email
        """
        self.member.membership_date = None
        self.member.membership_accepted = None
        self.member.certificate_email_date = None
        self.member.certificate_token = None
        return self

    def set_membership(self):
        """
        Set the member's membership
        """
        self.member.membership_date = date(2019, 10, 8)
        self.member.membership_accepted = True
        return self

    def set_certificate_email_just_sent(self):
        """
        Set the member's attributes so that an certificate email was just sent
        """
        self.member.certificate_email_date = datetime.now()
        return self

    def set_no_certificate_email_sent(self):
        """
        Set the member's attributes so that no email was sent
        """
        self.member.certificate_email_date = None
        return self

    def set_outdated_certificate_email(self):
        """
        Set the member's attributes so that the certificate email is outdated
        for downloading the certificate
        """
        self.member.certificate_email_date = datetime.now() - timedelta(
            days=15)
        return self

    def set_certificate_token(self, token=u'cert-token-abc-zyx'):
        """
        Set the member's certificate token
        """
        self.member.certificate_token = token
        return self

    def test_certificate_pdf(self):
        """
        Test the certificate_pdf view.

        1. Success, member with recent certificate email
        2. Failure, member with outdated certificate email
        3. Failure, wrong certificate token
        4. Failure, no certificate token set
        5. Failure, no certificate email sent
        """
        self.log_out()

        # 1. Success, member with recent certificate email
        self.reset_member() \
            .set_membership() \
            .set_certificate_email_just_sent() \
            .set_certificate_token()

        response = self.testapp.get(
            '/cert/{member_id}/C3S_{name}_{token}.pdf'.format(
                member_id=self.member.id,
                name='some-name',
                token=self.member.certificate_token),
            status=200)

        self.assertTrue(len(response.body) > 50000)
        self.assertTrue(len(response.body) < 100000)

        # 2. Failure, member with outdated certificate email
        self.reset_member() \
            .set_membership() \
            .set_outdated_certificate_email() \
            .set_certificate_token()

        response = self.testapp.get(
            '/cert/{member_id}/C3S_{name}_{token}.pdf'.format(
                member_id=self.member.id,
                name='some-name',
                token=self.member.certificate_token),
            status=404)

        # 3. Failure, wrong certificate token
        wrong_token = 'not-the-correct-token'
        self.reset_member() \
            .set_membership() \
            .set_certificate_email_just_sent() \
            .set_certificate_token()

        response = self.testapp.get(
            '/cert/{member_id}/C3S_{name}_{token}.pdf'.format(
                member_id=self.member.id, name='some-name', token=wrong_token),
            status=404)

        # 4. Failure, no certificate token set
        self.reset_member() \
            .set_membership() \
            .set_certificate_email_just_sent() \
            .set_certificate_token(None)

        response = self.testapp.get(
            '/cert/{member_id}/C3S_{name}_{token}.pdf'.format(
                member_id=self.member.id, name='some-name', token=wrong_token),
            status=404)

        # 5. Failure, no certificate email sent
        self.reset_member() \
            .set_membership() \
            .set_no_certificate_email_sent() \
            .set_certificate_token()

        response = self.testapp.get(
            '/cert/{member_id}/C3S_{name}_{token}.pdf'.format(
                member_id=self.member.id,
                name='some-name',
                token=self.member.certificate_token),
            status=404)
