# -*- coding: utf-8  -*-
"""
Tests the utils package.
"""

from datetime import date
import os
import transaction
import unittest

from pyramid import testing

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.models import C3sMember
import c3smembership.utils as utils


class TestUtilities(unittest.TestCase):
    """
    Tests the utils package
    """

    def setUp(self):
        """
        Set up database and engine
        """
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
        except:
            pass
        from sqlalchemy import create_engine
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        self.session = DBSession

        Base.metadata.create_all(engine)
        with transaction.manager:
            # German member
            member1 = C3sMember(
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u'addr one',
                address2=u'addr two',
                postcode=u'12345',
                city=u'Footown Mäh',
                country=u'Foocountry',
                locale=u'DE',
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAR',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u'GEMA',
                num_shares=u'23',
            )
            DBSession.add(member1)
            DBSession.flush()

    def tearDown(self):
        """
        Clean up database
        """
        DBSession.close()
        DBSession.remove()
        testing.tearDown()

    def test_generate_pdf_en(self):
        """
        Test pdf generation and resulting pdf size
        """
        from c3smembership.utils import generate_pdf

        mock_appstruct = {
            'firstname': u'Anne',
            'lastname': u'Gilles',
            'email': u'devnull@c3s.cc',
            'email_confirm_code': u'1234567890',
            'date_of_birth': '1987-06-05',
            'address1': 'addr one',
            'address2': 'addr two',
            'postcode': u'54321',
            'city': u'Müsterstädt',
            'country': u'some country',
            'member_of_colsoc': 'member_of_colsoc',
            'name_of_colsoc': 'Foo Colsoc',
            'membership_type': u'investing',
            'num_shares': '42',
            'locale': 'en',
            'date_of_submission': '2013-09-09 08:44:47.251588',
        }

        # a skipTest iff pdftk is not installed
        import subprocess
        from subprocess import CalledProcessError
        try:
            res = subprocess.check_call(
                ['which', 'pdftk'], stdout=open(os.devnull, 'w'))
            if res == 0:
                # go ahead with the tests
                result = generate_pdf(mock_appstruct)

                self.assertEquals(result.content_type,
                                  'application/pdf')
                # check pdf size
                self.assertTrue(210000 > len(result.body) > 50000)
                # TODO: check pdf for contents

        except CalledProcessError, cpe:
            pass

    def test_generate_pdf_de(self):
        """
        Test pdf generation
        and resulting pdf size
        """
        from c3smembership.utils import generate_pdf

        mock_appstruct = {
            'firstname': u'Anne',
            'lastname': u'Gilles',
            'address1': u'addr one',
            'address2': u'addr two',
            'postcode': u'54321',
            'city': u'Müsterstädt',
            'email': u'devnull@c3s.cc',
            'email_confirm_code': u'1234567890',
            'date_of_birth': u'1987-06-05',
            'country': u'my country',
            'membership_type': u'investing',
            'num_shares': u'23',
            'locale': 'de',
            'date_of_submission': '2013-09-09 08:44:47.251588',
        }

        # a skipTest iff pdftk is not installed
        import subprocess
        from subprocess import CalledProcessError
        try:
            res = subprocess.check_call(
                ['which', 'pdftk'], stdout=open(os.devnull, 'w'))
            if res == 0:
                result = generate_pdf(mock_appstruct)
                self.assertEquals(result.content_type,
                                  'application/pdf')
                self.assertTrue(210000 > len(result.body) > 50000)
                # TODO: check pdf for contents

        except CalledProcessError, cpe:
            pass

    def test_mail_body(self):
        """
        Test if mail body is constructed correctly and if umlauts work
        """
        from c3smembership.utils import make_mail_body
        import datetime
        dob = datetime.date(1999, 1, 1)
        member = C3sMember(
            firstname=u'Jöhn test_mail_body',
            lastname=u'Döe',
            email=u'devnull@c3s.cc',
            password=u'very_unsecure_password',
            address1=u'addr one',
            address2=u'addr two',
            postcode=u'12345 xyz',
            city=u'Town',
            country=u'af',
            locale=u'en',
            date_of_birth=dob,
            email_is_confirmed=False,
            email_confirm_code=u'1234567890',
            num_shares=u'23',
            date_of_submission=datetime.datetime.now(),
            membership_type=u'investing',
            member_of_colsoc=u'yes',
            name_of_colsoc=u'Buma',
            privacy_consent=datetime.datetime.now(),
        )
        result = make_mail_body(member)

        self.failUnless(u'Jöhn test_mail_body' in result)
        self.failUnless(u'Döe' in result)
        self.failUnless(u'postcode:                       12345 xyz' in result)
        self.failUnless(u'Town' in result)
        self.failUnless(u'devnull@c3s.cc' in result)
        self.failUnless(u'af' in result)
        self.failUnless(u'number of shares                23' in result)
        self.failUnless(
            u'member of coll. soc.:           yes' in result)
        self.failUnless(u'that\'s it.. bye!' in result)

    def test_create_accountant_mail(self):
        """
        Test creation of email message object
        """
        from c3smembership.utils import create_accountant_mail
        import datetime
        member = C3sMember(
            firstname=u'Jöhn test_create_accountant_mail',
            lastname=u'Doe',
            email=u'devnull@example.com',
            password=u'very_unsecure_password',
            address1='address part one',
            address2='address part two',
            postcode='POSTCODE',
            city=u'Town',
            country=u'af',
            locale=u'en',
            date_of_birth=datetime.date(1987, 6, 5),
            email_is_confirmed=False,
            email_confirm_code='ABCDEFGH',
            num_shares=7,
            date_of_submission=datetime.datetime.now(),
            membership_type=u'normal',
            member_of_colsoc=u'yes',
            name_of_colsoc=u'Foo Colsoc',
            privacy_consent=datetime.datetime.now(),
        )
        result = create_accountant_mail(member, ['yes@c3s.cc'])

        from pyramid_mailer.message import Message

        self.assertTrue(isinstance(result, Message))
        self.assertTrue('yes@c3s.cc' in result.recipients)
        self.failUnless('-BEGIN PGP MESSAGE-' in result.body,
                        'something missing in the mail body!')
        self.failUnless('-END PGP MESSAGE-' in result.body,
                        'something missing in the mail body!')
        self.failUnless(
            '[C3S] Yes! a new member' in result.subject,
            'something missing in the mail subject!')
        self.failUnless('noreply@c3s.cc' == result.sender,
                        'something missing in the mail body!')
