# -*- coding: utf-8 -*-
import unittest
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.mail_utils import get_salutation
from datetime import date


class TestMailUtils(unittest.TestCase):

    def setUp(self):
        self.member = C3sMember(
            firstname='SomeFirstnäme',
            lastname='Memberßhip Applicant',
            email='some@shri.de',
            address1="addr one",
            address2="addr two",
            postcode="12345",
            city="Footown Mäh",
            country="Foocountry",
            locale="DE",
            date_of_birth=date(1970, 1, 1),
            email_is_confirmed=False,
            email_confirm_code='ABCDEFGFOO',
            password='arandompassword',
            date_of_submission=date(2015, 1, 1),
            membership_type='normal',
            member_of_colsoc=True,
            name_of_colsoc="GEMA",
            num_shares='23',
        )

    def test_get_salutation(self):
        self.member.firstname = 'firßtname'
        self.member.lastname = 'lastnäme'
        self.member.is_legalentity = False
        self.assertEqual(get_salutation(self.member), 'firßtname lastnäme')

        self.member.firstname = 'firßtname'
        self.member.is_legalentity = True
        self.assertEqual(get_salutation(self.member), 'firßtname')
