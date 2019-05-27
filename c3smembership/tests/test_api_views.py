# -*- coding: utf-8 -*-

"""
Tests the API for c3sPartyTicketing.
"""


from datetime import date
import json
import unittest

from sqlalchemy import engine_from_config
from pyramid import testing
import transaction
from webtest import TestApp

from c3smembership import main
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.general_assembly_repository import \
    GeneralAssemblyRepository


GENERAL_ASSEMBLY = 7


class TestApiViews(unittest.TestCase):
    """
    Tests the ApiViews class.
    """

    def setUp(self):
        my_settings = {
            'sqlalchemy.url': 'sqlite:///:memory:',
            'api_auth_token': u"SECRETAUTHTOKEN",
        }
        self.config = testing.setUp()
        app = main({}, **my_settings)
        # set up the database
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(  # german
                firstname=u'SomeFirstnäme',
                lastname=u'SomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGFOO',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
        member1.membership_number = 'M1'
        # pylint: disable=no-member
        DBSession.add(member1)
        GeneralAssemblyRepository.invite_member(
            member1.membership_number, GENERAL_ASSEMBLY, u'MEMBERS_TOKEN')
        # pylint: disable=no-member
        DBSession.flush()

        self.testapp = TestApp(app)

    def tearDown(self):
        testing.tearDown()
        # pylint: disable=no-member
        DBSession.close()
        DBSession.remove()

    def test_api_userinfo(self):
        """
        Test the api_userinfo service.

        * must be a PUT, not a GET request
        * the auth header must be present
        * returns None if members refcode does not match
        * returns firstname, lastname, email, membership type
        """
        # try a GET -- must fail
        res = self.testapp.get('/lm', status=405)
        self.assertTrue('405 Method Not Allowed' in res.body.decode())
        self.assertTrue('The method GET is not allowed for this resource.'
                        in res.body.decode())

        # try a PUT -- fails under certain conditions
        with self.assertRaises(ValueError):
            res = self.testapp.put('/lm', status=200)
            # ValueError: No JSON object could be decoded

        # try a PUT -- fails under certain conditions
        with self.assertRaises(KeyError):
            res = self.testapp.put_json(
                '/lm', dict(id=1))  # status=200)
            # KeyError: 'token'
        # missing auth token -- must fail
        with self.assertRaises(KeyError):
            res = self.testapp.put_json(
                '/lm', dict(token=1))  # status=200)
            # KeyError: 'HTTP_X_MESSAGING_TOKEN'

        # try false auth token -- must fail: 401 unauthorized
        _headers = {'X-messaging-token': 'bar'}
        res = self.testapp.put_json(
            '/lm', dict(token=1), headers=_headers, status=401)

        # now use the correct auth token
        _auth_info = {'X-messaging-token': 'SECRETAUTHTOKEN'}

        # ..but a non-existing refcode
        # returns no user (None)
        res = self.testapp.put_json(
            '/lm', dict(token='foo'), headers=_auth_info, status=200)
        # body: {"lastname": "None", "firstname": "None"}
        self.assertTrue(json.loads(res.body)['firstname'], "None")
        self.assertTrue(json.loads(res.body)['lastname'], "None")

        self.testapp.reset()

        member1 = C3sMember.get_by_id(1)  # load member from DB for crosscheck

        # now try a valid refcode
        res2 = self.testapp.put_json(
            '/lm', dict(token='MEMBERS_TOKEN'),
            headers=_auth_info, status=200)
        self.assertTrue(json.loads(res2.body)['firstname'], member1.firstname)
        self.assertTrue(json.loads(res2.body)['lastname'], member1.lastname)
        self.assertTrue(json.loads(res2.body)['email'], member1.email)
        self.assertTrue(
            json.loads(res2.body)['mtype'], member1.membership_type)
