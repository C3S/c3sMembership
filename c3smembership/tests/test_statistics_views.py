# -*- coding: utf-8 -*-

from datetime import date
import unittest
from pyramid import testing
from sqlalchemy import create_engine
import transaction

from c3smembership.data.model.base import (
    Base,
    DBSession,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff


class TestViews(unittest.TestCase):
    """
    very basic tests for the main views
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        engine = create_engine('sqlite://')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(
                firstname='firsie',
                lastname='lastie',
                email='some@shri.de',
                address1="addr one",
                address2="addr two",
                postcode="12345",
                city="Footown Mäh",
                country="Foocountry",
                locale="de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGFOO',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc="GEMA",
                num_shares='23',
            )
            member2 = C3sMember(  # german
                firstname='AAASomeFirstnäme',
                lastname='XXXSomeLastnäme',
                email='some@shri.de',
                address1="addr one",
                address2="addr two",
                postcode="12345",
                city="Footown Mäh",
                country="Foocountry",
                locale="de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGBAR',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='normal',
                member_of_colsoc=True,
                name_of_colsoc="GEMA",
                num_shares='23',
            )
            member3 = C3sMember(  # german
                firstname='BBBSomeFirstnäme',
                lastname='AAASomeLastnäme',
                email='some@shri.de',
                address1="addr one",
                address2="addr two",
                postcode="12345",
                city="Footown Mäh",
                country="Foocountry",
                locale="de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code='ABCDEFGBAZ',
                password='arandompassword',
                date_of_submission=date.today(),
                membership_type='investing',
                member_of_colsoc=True,
                name_of_colsoc="GEMA",
                num_shares=23,
            )
            DBSession.add(member1)
            DBSession.add(member2)
            DBSession.add(member3)

            accountants_group = Group(name="staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                # print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = Staff(
                login="rut",
                password="berries",
                email="noreply@example.com",
            )
            staffer1.groups = [accountants_group]
            try:
                DBSession.add(accountants_group)
                DBSession.add(staffer1)
                DBSession.flush()
            except:
                print("it borked! (rut)")
                # pass

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_stats_view(self):
        """
        test the statistics view
        """
        from c3smembership.presentation.views.statistics import stats_view
        self.config.add_route('join', '/')
        request = testing.DummyRequest()

        class ShareInformationDummy(object):

            def __init__(self, share_count):
                self.share_count = share_count

            def get_share_count(self):
                return self.share_count

        request.registry.share_information = ShareInformationDummy(123)
        result = stats_view(request)
        self.assertTrue(result['num_shares_members'] == 123)
        self.assertTrue(result['num_staff'] == 1)
        self.assertTrue(result['_number_of_datasets'] == 3)
        self.assertTrue(result['num_members_accepted'] == 0)
        self.assertTrue(result['num_memnums'] == 0)
        self.assertTrue(result['next_memnum'] == 1)
        self.assertTrue(result['num_countries'] == 1)
        # self.assertTrue(result['num_staff'] == 1)
        # self.assertTrue(result['firstname'] is 'foo')
        #
        # this test would nicer results if some of the
        # datasets were accepted members...
