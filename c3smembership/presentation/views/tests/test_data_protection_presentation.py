# -*- coding: utf-8 -*-
"""
Tests the data_protection view module.
"""

from datetime import date
import unittest
from unittest import mock

from pyramid import testing
from sqlalchemy import engine_from_config
import transaction
from webob.multidict import MultiDict

from c3smembership.business.data_protection import DataProtection
from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.repository.dues_invoice_repository import \
    DuesInvoiceRepository
from c3smembership.data.repository.member_repository import MemberRepository
from c3smembership.presentation.views.data_protection import (
    data_protection_view,
)


class UserDummy(object):
    """
    Dummy for request.user providing a login name.
    """

    def __init__(self, login):
        self.login = login


def create_member(email_confirm_code, date_of_submission):
    """
    Create a C3sMember dataset for testing.
    """
    return C3sMember(
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
        date_of_submission=date_of_submission,
        membership_type=u'normal',
        member_of_colsoc=False,
        name_of_colsoc=u'',
        num_shares=1,
    )


class TestDataProtectionView(unittest.TestCase):
    """
    Tests the data_protection_view.
    """

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_route('data_protection', '/data_protection')
        self.config.add_route('detail', '/detail/{member_id}')
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

        self.dues_invoice_archiving = mock.Mock()
        self.dues_invoice_archiving.remove_archived_invoices.return_value = []
        self.config.registry.data_protection = DataProtection(
            MemberRepository,
            DuesInvoiceRepository,
            self.dues_invoice_archiving)

        with transaction.manager:
            # id 1: stale application, submitted long ago
            DBSession.add(
                create_member(u'STALE1', date(2015, 1, 1)))
            # id 2: recent application, still within retention
            DBSession.add(
                create_member(u'RECENT1', date.today()))
            # id 3: former member past retention
            lost = create_member(u'LOST1', date(2009, 1, 1))
            lost.membership_accepted = True
            lost.membership_number = 42
            lost.membership_date = date(2009, 6, 1)
            lost.membership_loss_date = date(2010, 12, 31)
            lost.membership_loss_type = u'resignation'
            DBSession.add(lost)

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()
        testing.tearDown()

    def make_post_request(self, member_ids, confirmed=True):
        """
        Create a dummy POST request for the data protection view.
        """
        post = MultiDict()
        post['anonymization_confirmed'] = '1' if confirmed else '0'
        for member_id in member_ids:
            post.add('member_id', str(member_id))
        request = testing.DummyRequest(post=post)
        request.user = UserDummy(u'staffer1')
        return request

    def test_get_candidates(self):
        """
        The view lists former members past retention and stale
        applications.
        """
        request = testing.DummyRequest()
        request.user = UserDummy(u'staffer1')
        result = data_protection_view(request)

        self.assertEqual(len(result['lost_members']), 1)
        self.assertEqual(result['lost_members'][0].membership_number, 42)
        self.assertEqual(len(result['stale_applications']), 1)
        self.assertEqual(
            result['stale_applications'][0].email_confirm_code, u'STALE1')

    def test_post_not_confirmed(self):
        """
        Without confirmation nothing is anonymized.
        """
        request = self.make_post_request([1], confirmed=False)
        result = data_protection_view(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNone(C3sMember.get_by_id(1).anonymized)
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'not confirmed' in messages[0])

    def test_post_nothing_selected(self):
        """
        Without a selection nothing is anonymized.
        """
        request = self.make_post_request([])
        result = data_protection_view(request)

        self.assertEqual(result.status_code, 302)
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'selected' in messages[0])

    def test_post_anonymize(self):
        """
        Selected candidates are anonymized, non-candidates are refused.
        """
        # id 1 stale application (candidate), id 2 recent application
        # (refused), id 3 lost member past retention (candidate)
        request = self.make_post_request([1, 2, 3])
        result = data_protection_view(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNotNone(C3sMember.get_by_id(1).anonymized)
        self.assertIsNone(C3sMember.get_by_id(2).anonymized)
        self.assertIsNotNone(C3sMember.get_by_id(3).anonymized)

        success = request.session.pop_flash('success')
        self.assertEqual(len(success), 1)
        self.assertTrue(u'2 dataset(s) were anonymized' in success[0])
        danger = request.session.pop_flash('danger')
        self.assertEqual(len(danger), 1)
        self.assertTrue(u'1 dataset(s) were refused' in danger[0])

        # the ledger data of the anonymized member is kept
        member = C3sMember.get_by_id(3)
        self.assertEqual(member.membership_number, 42)
        self.assertIsNone(member.lastname)
