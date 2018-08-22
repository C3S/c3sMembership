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
        engine = create_engine(u'sqlite://')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)
        with transaction.manager:
            member1 = C3sMember(
                firstname=u'firsie',
                lastname=u'lastie',
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
            member2 = C3sMember(  # german
                firstname=u'AAASomeFirstnäme',
                lastname=u'XXXSomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAR',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'normal',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=u'23',
            )
            member3 = C3sMember(  # german
                firstname=u'BBBSomeFirstnäme',
                lastname=u'AAASomeLastnäme',
                email=u'some@shri.de',
                address1=u"addr one",
                address2=u"addr two",
                postcode=u"12345",
                city=u"Footown Mäh",
                country=u"Foocountry",
                locale=u"de",
                date_of_birth=date.today(),
                email_is_confirmed=False,
                email_confirm_code=u'ABCDEFGBAZ',
                password=u'arandompassword',
                date_of_submission=date.today(),
                membership_type=u'investing',
                member_of_colsoc=True,
                name_of_colsoc=u"GEMA",
                num_shares=23,
            )
            DBSession.add(member1)
            DBSession.add(member2)
            DBSession.add(member3)

            accountants_group = Group(name=u"staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                # print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = Staff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@example.com",
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
        # print result
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
