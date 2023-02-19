# -*- coding: utf-8  -*-
"""
Tests the utils package.
"""

import datetime
import os
import unittest

from pyramid import testing
from pyramid_mailer.message import Message
from sqlalchemy import create_engine
import subprocess
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.utils import (
    generate_pdf,
    create_accountant_mail,
    make_mail_body,
)


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
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        self.session = DBSession

        Base.metadata.create_all(engine)
        with transaction.manager:
            # German member
            member1 = C3sMember(
                firstname='SomeFirstnäme',
                lastname='SomeLastnäme',
                email='some@shri.de',
                address1='addr one',
                address2='addr two',
                postcode='12345',
                city='Footown Mäh',
                country='Foocountry',
                locale='DE',
                date_of_birth=datetime.date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGBAR',
                password='arandompassword',
                date_of_submission=datetime.date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc='GEMA',
                num_shares='23',
            )
            db_session = DBSession()
            db_session.add(member1)
            db_session.flush()

    def tearDown(self):
        """
        Clean up database
        """
        DBSession().close()
        DBSession.remove()
        testing.tearDown()

    def test_generate_pdf_en(self):
        """
        Test pdf generation and resulting pdf size
        """
        mock_appstruct = {
            'firstname': 'Anne',
            'lastname': 'Gilles',
            'email': 'devnull@example.com',
            'email_confirm_code': '1234567890',
            'date_of_birth': '1987-06-05',
            'address1': 'addr one',
            'address2': 'addr two',
            'postcode': '54321',
            'city': 'Müsterstädt',
            'country': 'some country',
            'member_of_colsoc': 'member_of_colsoc',
            'name_of_colsoc': 'Foo Colsoc',
            'membership_type': 'investing',
            'num_shares': '42',
            'locale': 'en',
            'date_of_submission': '2013-09-09 08:44:47.251588',
        }

        # a skipTest iff pdftk is not installed
        try:
            res = subprocess.check_call(
                ['which', 'pdftk'], stdout=open(os.devnull, 'w'))
            if res == 0:
                # go ahead with the tests
                request = testing.DummyRequest()
                result = generate_pdf(request, mock_appstruct)

                self.assertEqual(result.content_type,
                                  'application/pdf')
                # check pdf size
                self.assertTrue(210000 > len(result) > 50000)
        except subprocess.CalledProcessError:
            pass

    def test_generate_pdf_de(self):
        """
        Test pdf generation
        and resulting pdf size
        """

        request = testing.DummyRequest()
        appstruct = {
            'firstname': 'Anne',
            'lastname': 'Gilles',
            'address1': 'addr one',
            'address2': 'addr two',
            'postcode': '54321',
            'city': 'Müsterstädt',
            'email': 'devnull@example.com',
            'email_confirm_code': '1234567890',
            'date_of_birth': '1987-06-05',
            'country': 'my country',
            'membership_type': 'investing',
            'num_shares': '23',
            'locale': 'de',
            'date_of_submission': '2013-09-09 08:44:47.251588',
        }

        # a skipTest iff pdftk is not installed
        try:
            res = subprocess.check_call(
                ['which', 'pdftk'], stdout=open(os.devnull, 'w'))
            if res == 0:
                result = generate_pdf(request, appstruct)
                self.assertEqual(result.content_type,
                                  'application/pdf')
                self.assertTrue(210000 > len(result) > 50000)
        except subprocess.CalledProcessError:
            pass

    def test_mail_body(self):
        """
        Test if mail body is constructed correctly and if umlauts work
        """
        dob = datetime.date(1999, 1, 1)
        member = C3sMember(
            firstname='Jöhn test_mail_body',
            lastname='Döe',
            email='devnull@example.com',
            password='very_unsecure_password',
            address1='addr one',
            address2='addr two',
            postcode='12345 xyz',
            city='Town',
            country='af',
            locale='en',
            date_of_birth=dob,
            email_is_confirmed=False,
            email_confirm_code='1234567890',
            num_shares='23',
            date_of_submission=datetime.datetime.now(),
            membership_type='investing',
            member_of_colsoc='yes',
            name_of_colsoc='Buma',
            privacy_consent=datetime.datetime.now(),
        )
        result = make_mail_body(member)

        self.assertTrue('Jöhn test_mail_body' in result)
        self.assertTrue('Döe' in result)
        self.assertTrue('postcode:                       12345 xyz' in result)
        self.assertTrue('Town' in result)
        self.assertTrue('devnull@example.com' in result)
        self.assertTrue('af' in result)
        self.assertTrue('number of shares                23' in result)
        self.assertTrue(
            'member of coll. soc.:           yes' in result)
        self.assertTrue('that\'s it.. bye!' in result)

    def test_create_accountant_mail(self):
        """
        Test creation of email message object
        """
        member = C3sMember(
            firstname='Jöhn test_create_accountant_mail',
            lastname='Doe',
            email='devnull@example.com',
            password='very_unsecure_password',
            address1='address part one',
            address2='address part two',
            postcode='POSTCODE',
            city='Town',
            country='af',
            locale='en',
            date_of_birth=datetime.date(1987, 6, 5),
            email_is_confirmed=False,
            email_confirm_code='ABCDEFGH',
            num_shares=7,
            date_of_submission=datetime.datetime.now(),
            membership_type='normal',
            member_of_colsoc='yes',
            name_of_colsoc='Foo Colsoc',
            privacy_consent=datetime.datetime.now(),
        )
        result = create_accountant_mail(
            member, 'yes@example.com', ['yes@example.com'])

        self.assertTrue(isinstance(result, Message))
        self.assertTrue('yes@example.com' in result.recipients)
        self.assertTrue('-BEGIN PGP MESSAGE-' in result.body,
                        'something missing in the mail body!')
        self.assertTrue('-END PGP MESSAGE-' in result.body,
                        'something missing in the mail body!')
        self.assertTrue(
            '[C3S] Yes! a new member' in result.subject,
            'something missing in the mail subject!')
        self.assertEqual('yes@example.com', result.sender,
                         'something missing in the mail body!')
