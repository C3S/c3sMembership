# -*- coding: utf-8 -*-

import os
import sys
import transaction
from datetime import datetime, date

from sqlalchemy import engine_from_config
from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from alembic.config import Config
from alembic import command

from c3smembership.data.model.base import (
    DBSession,
    Base,
)
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base.group import Group
from c3smembership.data.model.base.staff import Staff

"""
this module holds database initialization code

when the webapp is installed, a database has to be initialized in order to
store form input (new members), but also to authenticate staff when loging in.

in setup.py there is a section 'console_scripts' under 'entry_points'.
thus a console script is created when the app is set up:

  env/bin/initialize_c3sMembership_db

the main function below is called...

we have different use cases:
(1) production:
        for production we need a clean database (initially no members)
        with accounts for staffers/accountants to auth their login.
        those credentials should not go into version control.
(2) testing
        for tests and demo purposes we need prepopulated databases:
        example users to check if the app works, and enough of them
        so staffers can check out pagination
"""

how_many = 7


def usage(argv):
    """
    print usage information if the script was called with bad arguments
    """
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    """
    initialize the database
    """
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    # Setup alembic database migration information.
    # This creates the alembic_version table in the database
    # which is the basis for migrations and the "alembic current"
    # command.
    alembic_cfg = Config('alembic.ini')
    command.stamp(alembic_cfg, 'head')
    # add some content
    with transaction.manager:
        # a group for accountants/staff
        accountants_group = Group(name=u"staff")
        try:
            DBSession.add(accountants_group)
            DBSession.flush()
        except:  # pragma: no cover
            print("could not add group staff.")
            # pass
    with transaction.manager:
        # staff personnel
        staffer1 = Staff(
            login=u"rut",
            password=u"berries",
            email=u"noreply@example.com",
        )
        staffer1.groups = [accountants_group]
        try:
            DBSession.add(staffer1)
            DBSession.flush()
        except:  # pragma: no cover
            print("it borked! (rut)")
    # one more staffer
    with transaction.manager:
        staffer2 = Staff(
            login=u"reel",
            password=u"boo",
            email=u"noreply@example.com",
        )
        staffer2.groups = [accountants_group]
        try:
            DBSession.add(staffer2)
            DBSession.flush()
        except:  # pragma: no cover
            print("it borked! (reel)")
    # a member, actually a membership form submission
    with transaction.manager:
        member1 = C3sMember(
            firstname=u"Firstnäme",  # includes umlaut
            lastname=u"Lastname",
            email=u"uat.yes@example.com",
            password=u"berries",
            address1=u"address one",
            address2=u"address two",
            postcode=u"12345 foo",
            city=u"Footown Mäh",
            country=u"Foocountry",
            locale=u"en",
            date_of_birth=date(1971, 02, 03),
            email_is_confirmed=False,
            email_confirm_code=u"ABCDEFGHIJ",
            num_shares=u'10',
            date_of_submission=datetime.now(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
        )
        try:
            DBSession.add(member1)
        except:  # pragma: no cover
            pass

    with transaction.manager:
        normal_de = C3sMember(  # german normal
            firstname=u'Ada Traumhaft',
            lastname=u'Musiziert',
            email=u'uat.yes@example.com',
            address1=u"Musikergasse 34",
            address2=u"Hinterhaus",
            postcode=u"12345",
            city=u"Foostadt Ada",
            country=u"Germany",
            locale=u"de",
            date_of_birth=date(1971, 3, 4),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE1',
            password=u'adasrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"GEMA",
            num_shares=u'23',
        )
        normal_en = C3sMember(  # english normal
            firstname=u'James',
            lastname=u'Musician',
            email=u'uat.yes@example.com',
            address1=u"james addr 1",
            address2=u"james appartment 2",
            postcode=u"12345",
            city=u"Jamestown",
            country=u"Jamescountry",
            locale=u"en",
            date_of_birth=date(1972, 4, 5),
            email_is_confirmed=False,
            email_confirm_code=u'NORMAL_DE',
            password=u'jamesrandompassword',
            date_of_submission=date.today(),
            membership_type=u'normal',
            member_of_colsoc=True,
            name_of_colsoc=u"",
            num_shares=u'2',
        )
        investing_de = C3sMember(  # german investing
            firstname=u'Herman',
            lastname=u'Investor',
            email=u'uat.yes@example.com',
            address1=u"c/o Mutti",
            address2=u"addr two4",
            postcode=u"12344",
            city=u"Footown M44",
            country=u"Austria",
            locale=u"de",
            date_of_birth=date(1974, 9, 8),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_DE',
            password=u'arandompasswor4',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'6',
        )
        investing_en = C3sMember(  # english investing
            firstname=u'Britany',
            lastname=u'Investing',
            email=u'uat.yes@example.com',
            address1=u"aone5",
            address2=u"atwo5",
            postcode=u"12355",
            city=u"London",
            country=u"United Kingdom",
            locale=u"en",
            date_of_birth=date(1978, 4, 1),
            email_is_confirmed=False,
            email_confirm_code=u'INVESTING_EN',
            password=u'arandompasswor5',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=True,
            name_of_colsoc=u"",
            num_shares=u'60',
        )
        legal_entity_de = C3sMember(  # german investing legal entity
            firstname=u'Günther Vorstand',
            lastname=u'Deutscher Musikverlag',
            email=u'uat.yes@example.com',
            address1=u"Ährenweg 1",
            address2=u"",
            postcode=u"98765",
            city=u"Teststadt",
            country=u"Germany",
            locale=u"de",
            date_of_birth=date(1987, 3, 6),
            email_is_confirmed=False,
            email_confirm_code=u'VERLAG_DE',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'60',
        )
        legal_entity_en = C3sMember(  # english investing legal entity
            firstname=u'John BigBoss',
            lastname=u'Some Company',
            email=u'uat.yes@example.com',
            address1=u"foo boulevard",
            address2=u"123-345",
            postcode=u"98765",
            city=u"London",
            country=u"United Kingdom",
            locale=u"en",
            date_of_birth=date(1982, 4, 2),
            email_is_confirmed=False,
            email_confirm_code=u'COMPANY_EN',
            password=u'arandompasswor6',
            date_of_submission=date.today(),
            membership_type=u'investing',
            member_of_colsoc=False,
            name_of_colsoc=u"",
            num_shares=u'60',
        )
        DBSession.add(normal_de)
        DBSession.add(normal_en)
        DBSession.add(investing_de)
        DBSession.add(investing_en)
        legal_entity_de.is_legalentity = True
        DBSession.add(legal_entity_de)
        legal_entity_en.is_legalentity = True
        DBSession.add(legal_entity_en)


def init():
    engine = engine_from_config({'sqlalchemy.url': 'sqlite:///:memory:'})
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    # Setup alembic database migration information.
    # This creates the alembic_version table in the database
    # which is the basis for migrations and the "alembic current"
    # command.
    alembic_cfg = Config('alembic.ini')
    command.stamp(alembic_cfg, 'head')
