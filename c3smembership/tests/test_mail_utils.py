# -*- coding: utf-8 -*-
import unittest
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.mail_utils import get_salutation
from datetime import date


class TestMailUtils(unittest.TestCase):

    def setUp(self):
        self.member = C3sMember(
            firstname=u'SomeFirstnäme',
            lastname=u'Memberßhip Applicant',
            email=u'some@shri.de',
            address1=u"addr one",
            address2=u"addr two",
            postcode=u"12345",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"DE",
            date_of_birth=date(1970, 1, 1),
            email_is_confirmed=False,
            email_confirm_code=u'ABCDEFGFOO',
            password=u'arandompassword',
            date_of_submission=date(2015, 1, 1),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'23',
        )

    def test_get_salutation(self):
        self.member.firstname = u'firßtname'
        self.member.lastname = u'lastnäme'
        self.member.is_legalentity = False
        self.assertEqual(get_salutation(self.member), u'firßtname lastnäme')

        self.member.firstname = u'firßtname'
        self.member.is_legalentity = True
        self.assertEqual(get_salutation(self.member), u'firßtname')
