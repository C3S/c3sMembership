# -*- coding: utf-8 -*-
"""
Tests the membership_member_delete module.

Deletion must only be possible for datasets which have not been accepted as
members. Accepted members are subject to statutory retention and must go
through the membership loss process.
"""

from datetime import date
import unittest

from pyramid import testing
from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.views.membership_member_delete import (
    delete_entry,
)


class UserDummy(object):
    """
    Dummy for request.user providing a login name.
    """

    def __init__(self, login):
        self.login = login


def create_member(email_confirm_code, membership_accepted=False):
    """
    Create a C3sMember dataset for testing.
    """
    member = C3sMember(
        firstname=u'SomeFirstnäme',
        lastname=u'SomeLastnäme',
        email=u'some@shri.de',
        address1=u'addr one',
        address2=u'addr two',
        postcode=u'12345',
        city=u'Footown Mäh',
        country=u'Foocountry',
        locale=u'DE',
        date_of_birth=date(1980, 1, 2),
        email_is_confirmed=False,
        email_confirm_code=email_confirm_code,
        password=u'arandompassword',
        date_of_submission=date.today(),
        membership_type=u'normal',
        member_of_colsoc=False,
        name_of_colsoc=u'',
        num_shares=1,
    )
    if membership_accepted:
        member.membership_accepted = True
        member.membership_date = date(2015, 1, 1)
        member.membership_number = 42
    return member


class TestDeleteEntry(unittest.TestCase):
    """
    Tests the delete_entry view.
    """

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_route('dashboard', '/dashboard')
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            # id 1: application, not accepted
            DBSession.add(create_member(u'APPLICANT1'))
            # id 2: accepted member
            DBSession.add(
                create_member(u'MEMBER1', membership_accepted=True))

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()
        testing.tearDown()

    @staticmethod
    def make_request(memberid, deletion_confirmed=True):
        """
        Create a dummy request for the delete_entry view.
        """
        params = {}
        if deletion_confirmed:
            params['deletion_confirmed'] = '1'
        request = testing.DummyRequest(
            matchdict={'memberid': memberid},
            params=params)
        request.user = UserDummy(u'staffer1')
        return request

    def test_delete_application(self):
        """
        A dataset without accepted membership can be deleted.
        """
        request = self.make_request(1)
        result = delete_entry(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNone(C3sMember.get_by_id(1))
        messages = request.session.pop_flash('success')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'was deleted' in messages[0])

    def test_delete_accepted_member_refused(self):
        """
        A dataset with accepted membership must not be deleted.
        """
        request = self.make_request(2)
        result = delete_entry(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(C3sMember.get_by_id(2))
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'membership loss' in messages[0])

    def test_delete_nonexistent_member(self):
        """
        Deleting a nonexistent member id must not fail.
        """
        request = self.make_request(123)
        result = delete_entry(request)

        self.assertEqual(result.status_code, 302)
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'does not exist' in messages[0])

    def test_delete_not_confirmed(self):
        """
        Without confirmation nothing is deleted.
        """
        request = self.make_request(1, deletion_confirmed=False)
        result = delete_entry(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(C3sMember.get_by_id(1))
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'not confirmed' in messages[0])
