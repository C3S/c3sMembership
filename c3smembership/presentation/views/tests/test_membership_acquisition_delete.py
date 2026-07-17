# -*- coding: utf-8 -*-
"""
Tests the delete_afms view of the membership_acquisition module.

Bulk deletion must skip datasets which have been accepted as members.
"""

import unittest

from pyramid import testing
from sqlalchemy import engine_from_config
import transaction

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.presentation.views.membership_acquisition import delete_afms
from c3smembership.presentation.views.tests.test_membership_member_delete \
    import (
        create_member,
        UserDummy,
    )


class TestDeleteAfms(unittest.TestCase):
    """
    Tests the delete_afms view.
    """

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_route('dashboard', '/dashboard')
        my_settings = {'sqlalchemy.url': 'sqlite:///:memory:', }
        engine = engine_from_config(my_settings)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            # ids 1 and 3: applications, not accepted; id 2: accepted member
            DBSession.add(create_member(u'APPLICANT1'))
            DBSession.add(
                create_member(u'MEMBER1', membership_accepted=True))
            DBSession.add(create_member(u'APPLICANT2'))

    def tearDown(self):
        # pylint: disable=no-member
        DBSession.close()
        # pylint: disable=no-member
        DBSession.remove()
        testing.tearDown()

    def test_delete_range_skips_accepted(self):
        """
        Deleting a range deletes applications but skips accepted members.
        """
        request = testing.DummyRequest(post={'first': '1', 'last': '3'})
        request.user = UserDummy(u'staffer1')
        result = delete_afms(request)

        self.assertEqual(result.status_code, 302)
        self.assertIsNone(C3sMember.get_by_id(1))
        self.assertIsNotNone(C3sMember.get_by_id(2))
        self.assertIsNone(C3sMember.get_by_id(3))
        messages = request.session.pop_flash('danger')
        self.assertEqual(len(messages), 1)
        self.assertTrue(u'2' in messages[0])
        self.assertTrue(u'membership loss' in messages[0])

    def test_form_rendering(self):
        """
        Without POST data the deletion form is rendered.
        """
        request = testing.DummyRequest()
        request.user = UserDummy(u'staffer1')
        result = delete_afms(request)

        self.assertTrue('delete_form' in result)
