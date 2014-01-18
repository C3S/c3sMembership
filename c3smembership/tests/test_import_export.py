# -*- coding: utf-8 -*-
import re
import os
import unittest
import tempfile
import unicodecsv
from pyramid import testing
from c3smembership.models import (
    DBSession,
    Base,
    C3sMember,
    C3sStaff,
    Group,
)
from sqlalchemy import engine_from_config
import transaction
from datetime import (
    date,
    datetime,
)


class ImportExportTests(unittest.TestCase):
    """
    check import of CVS data
    """
    def setUp(self):
        self.config = testing.setUp()
        self.config.include('pyramid_mailer.testing')
        try:
            DBSession.close()
            DBSession.remove()
            #print "closed and removed DBSession"
        except:
            pass
            #print "no session to close"
        try:
            os.remove('test_import.db')
            #print "deleted old test database"
        except:
            pass
            #print "never mind"
       # self.session = DBSession()
        my_settings = {
            'sqlalchemy.url': 'sqlite:///test_import.db',
            'available_languages': 'da de en es fr',
            'c3smembership.dashboard_number': '30'}
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
                locale=u"DE",
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
            DBSession.add(member1)
            DBSession.flush()
            self.m1_last_pw_change = member1.last_password_change
        with transaction.manager:
                # a group for accountants/staff
            accountants_group = Group(name=u"staff")
            try:
                DBSession.add(accountants_group)
                DBSession.flush()
                print("adding group staff")
            except:
                print("could not add group staff.")
                # pass
            # staff personnel
            staffer1 = C3sStaff(
                login=u"rut",
                password=u"berries",
                email=u"noreply@c3s.cc",
            )
            staffer1.groups = [accountants_group]
            try:
                DBSession.add(accountants_group)
                DBSession.add(staffer1)
                DBSession.flush()
            except:
                print("it borked! (rut)")
                # pass

        from c3smembership import main
        app = main({}, **my_settings)
        from webtest import TestApp
        self.testapp = TestApp(app)

    def tearDown(self):
        DBSession.close()
        DBSession.remove()
        #os.remove('test_import.db')
        testing.tearDown()

    def test_import(self):
        """
        load the login form, dashboard, start import, check outcome
        """
        # try unauthenticated
        res = self.testapp.get('/import_all', status=403)  # 403: forbidden
        #print res.body
        #
        # login
        #
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user, valid password
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        #
        #print(res2.body)
        # being logged in ...
        res3 = res2.follow()
        res3 = res3.follow()
        print '-#-' * 10
        print res3.body
        self.failUnless(
            'Dashboard' in res3.body)
        # now try authenticated
        res = self.testapp.get('/import_all', status=302)
        res2 = res.follow()
        #print res2.body

        # XXX check database contents
        how_many = C3sMember.get_number()
        self.assertTrue(how_many is 3)
        crowd = C3sMember.member_listing(
            "id", how_many=C3sMember.get_number(), order="asc")
        #import pdb; pdb.set_trace()
        self.assertTrue(u'SomeFirstnäme' in crowd[0].firstname)
        self.assertTrue('Alice' in crowd[1].firstname)
        self.assertTrue(u'Göbel' in crowd[1].lastname)
        self.assertTrue('schmoo@example.com' in crowd[1].email)
        self.assertTrue(
            str(
                datetime.strptime(
                    '2013-12-26 13:33:37.422342',
                    '%Y-%m-%d %H:%M:%S.%f')
            ) in str(crowd[1].last_password_change))
        self.assertTrue(u'Horstmüller-Str. 16' in crowd[1].address1)
        self.assertTrue('' in crowd[1].address2)
        self.assertTrue('12345' in crowd[1].postcode)
        self.assertTrue('Hamburg' in crowd[1].city)
        self.assertTrue('DE' in crowd[1].country)
        self.assertTrue('de' in crowd[1].locale)
        self.assertTrue('1951-04-05' in str(crowd[1].date_of_birth))
        self.assertFalse(crowd[1].email_is_confirmed)
        self.assertTrue('SJWAI666LU' in crowd[1].email_confirm_code)
        self.assertTrue(crowd[1].num_shares is 1)
        self.assertTrue(
            '2013-12-29 15:30:23.422342' in str(crowd[1].date_of_submission))
        self.assertTrue('normal' in crowd[1].membership_type)
        self.assertFalse(crowd[1].member_of_colsoc)
        self.assertTrue('' in crowd[1].name_of_colsoc)
        self.assertTrue(crowd[1].signature_received)
        self.assertTrue(
            '2013-12-29 21:28:45.364342' in str(
                crowd[1].signature_received_date))
        self.assertFalse(crowd[1].payment_received)
        self.assertTrue(
            '1970-01-01 00:00:00' in str(crowd[1].payment_received_date))
        self.assertFalse(crowd[1].signature_confirmed)
        self.assertTrue(
            '1970-01-01 00:00:00' in str(
                crowd[1].signature_confirmed_date))
        self.assertFalse(crowd[1].payment_confirmed)
        self.assertTrue(
            '1970-01-01 00:00:00' in str(
                crowd[1].payment_confirmed_date))
        self.assertTrue('' in crowd[1].accountant_comment)
        #
        # test another row
        #
        self.assertTrue('Alize' in crowd[2].firstname)
        self.assertTrue(u'Görbel' in crowd[2].lastname)
        self.assertTrue('schmo@example.com' in crowd[2].email)
        self.assertTrue(
            str(
                datetime.strptime(
                    '2013-12-26 13:33:37.422342',
                    '%Y-%m-%d %H:%M:%S.%f'))
            in str(crowd[1].last_password_change))
        self.assertTrue(u'Horstmüller-Str. 23' in crowd[2].address1)
        self.assertTrue('addr2' in crowd[2].address2)
        self.assertTrue('12345' in crowd[2].postcode)
        self.assertTrue('Hamburg' in crowd[2].city)
        self.assertTrue('FR' in crowd[2].country)
        self.assertTrue('fr' in crowd[2].locale)
        self.assertTrue('1951-04-06' in str(crowd[2].date_of_birth))
        self.assertTrue(crowd[2].email_is_confirmed)
        self.assertTrue('SJWAI666LT' in crowd[2].email_confirm_code)
        self.assertTrue(crowd[2].num_shares is 2)
        self.assertTrue(
            '2013-12-29 15:30:42.422342' in str(crowd[2].date_of_submission))
        self.assertTrue('investing' in crowd[2].membership_type)
        self.assertTrue(crowd[2].member_of_colsoc)
        self.assertTrue('GEMA' in crowd[2].name_of_colsoc)
        self.assertTrue(crowd[2].signature_received)
        self.assertTrue(
            '2013-12-29 21:28:45.364323' in str(
                crowd[2].signature_received_date))
        self.assertTrue(crowd[2].payment_received)
        self.assertTrue(
            '1970-01-01 00:00:01' in str(crowd[2].payment_received_date))
        self.assertTrue(crowd[2].signature_confirmed)
        self.assertTrue(
            '1970-01-01 00:00:02' in str(
                crowd[2].signature_confirmed_date))
        self.assertTrue(crowd[2].payment_confirmed)
        self.assertTrue(
            '1970-01-01 00:00:03' in str(
                crowd[2].payment_confirmed_date))
        self.assertTrue('30c3' in crowd[2].accountant_comment)

    def test_export(self):
        """
        load the login form, dashboard, start export, check outcome
        """
        # try unauthenticated
        res = self.testapp.get('/export_all', status=403)  # 403: forbidden
        # login
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user, valid password
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        #
        print('-'*30)
        #print(res2.body)
        # being logged in ...
        res3 = res2.follow()
        res3 = res3.follow()

        self.failUnless(
            'Dashboard' in res3.body)
        # now try authenticated
        export = tempfile.NamedTemporaryFile()
        export.write(self.testapp.get('/export_all', status=200).body)
        export.seek(0)  # rewind to start

        r = unicodecsv.reader(export.file, delimiter=';',
                              encoding='utf-8',
                              quoting=unicodecsv.QUOTE_ALL)
        header = r.next()
        # check header consistency
        self.assertTrue(
            header == [
                u'firstname', u'lastname', u'email',  # 1, 2, 3
                u'password', u'last_password_change',  # 3, 4
                u'address1', u'address2', u'postcode', u'city', u'country',
                u'locale', u'date_of_birth',  # 10, 11
                u'email_is_confirmed', u'email_confirm_code',  # 12, 13
                u'num_shares', u'date_of_submission',  # 14, 15
                u'membership_type',  # 16
                u'member_of_colsoc', u'name_of_colsoc',
                u'signature_received', u'signature_received_date',
                u'payment_received', u'payment_received_date',
                u'signature_confirmed', u'signature_confirmed_date',
                u'payment_confirmed', u'payment_confirmed_date',
                u'accountant_comment']
        )

        # check/compare database contents
        r1 = r.next()  # get next row fom CSV
        how_many = C3sMember.get_number()
        self.assertTrue(how_many is 1)
        crowd = C3sMember.member_listing(
            "id", how_many=C3sMember.get_number(), order="desc")

        self.assertTrue(u'SomeFirstnäme' in crowd[0].firstname)
        self.assertTrue(r1[0] in crowd[0].firstname)
        self.assertTrue(u'SomeLastnäme' in crowd[0].lastname)
        self.assertTrue(r1[1] in crowd[0].lastname)
        self.assertTrue('some@shri.de' in crowd[0].email)
        self.assertTrue(r1[2] in crowd[0].email)

        self.assertTrue(str(r1[4]) in str(self.m1_last_pw_change))
        self.assertTrue(r1[5] in crowd[0].address1)
        self.assertTrue(r1[6] in crowd[0].address2)
        self.assertTrue(r1[7] in crowd[0].postcode)
        self.assertTrue(r1[8] in crowd[0].city)
        self.assertTrue(r1[9] in crowd[0].country)
        self.assertTrue(r1[10] in crowd[0].locale)
        self.assertTrue(r1[11] in str(crowd[0].date_of_birth))
        self.assertFalse(crowd[0].email_is_confirmed)
        self.assertTrue(r1[12] in u"False")
        self.assertTrue(r1[13] in crowd[0].email_confirm_code)
        self.assertTrue(str(r1[14]) == str(crowd[0].num_shares))
        self.assertTrue(
            r1[15] in str(crowd[0].date_of_submission))
        self.assertTrue('normal' in crowd[0].membership_type)
        self.assertTrue(r1[16] in crowd[0].membership_type)
        self.assertTrue(crowd[0].member_of_colsoc)
        self.assertTrue(r1[17] in "True")
        self.assertTrue(r1[18] in crowd[0].name_of_colsoc)
        self.assertTrue(crowd[0].name_of_colsoc in r1[18])
        self.assertTrue(str(r1[19]) in str(crowd[0].signature_received))
        self.assertTrue(
            r1[20] in str(
                crowd[0].signature_received_date))
        self.assertFalse(crowd[0].payment_received)
        self.assertTrue(str(r1[21]) in u'False')
        #print r1[22]
        # self.assertTrue(
        #     '1970-01-01 00:00:00' in str(crowd[0].payment_received_date))
        #print r1[23]
        # self.assertFalse(crowd[0].signature_confirmed)
        #print r1[24]
        # self.assertTrue(
        #     '1970-01-01 00:00:00' in str(
        #         crowd[0].signature_confirmed_date))
        #print r1[25]
        # self.assertFalse(crowd[0].payment_confirmed)
        #print r1[26]
        # self.assertTrue(
        #     '1970-01-01 00:00:00' in str(
        #         crowd[0].payment_confirmed_date))
        #print r1[27]
        self.assertTrue('' in r1[27])
        #self.assertTrue('' in crowd[0].accountant_comment)

    def test_import_equals_export(self):
        """
        load the login form, dashboard, start import, then export,
        check outcome: same?
        """
        # login
        res = self.testapp.get('/login', status=200)
        self.failUnless('login' in res.body)
        # try valid user, valid password
        form = res.form
        form['login'] = 'rut'
        form['password'] = 'berries'
        res2 = form.submit('submit', status=302)
        # being logged in ...
        res3 = res2.follow()
        res3 = res3.follow()
        self.failUnless(
            'Dashboard' in res3.body)
        # delete existing entry
        self.assertTrue('Number of data sets: 1' in res3.body)
        del1 = self.testapp.get('/delete/1', status=302)
        res = del1.follow()
        res = res.follow()
        self.assertTrue('Number of data sets: 0' in res.body)
        # import CSV
        res2 = self.testapp.get('/import_all', status=302)
        res3 = res2.follow()
        res3 = res3.follow()
        self.assertTrue('Number of data sets: 2' in res3.body)
        _export = self.testapp.get('/export_all', status=200)
        # compare import and export

        # remove password hash from import
        with open('import/import.csv', 'r') as import_file:
            _import = import_file.read()
        #print _import
        _import = _import.split(';')
        _import_cleaned = ''
        for item in _import:
            if not item.startswith('"$2a$10'):
                _import_cleaned = ';'.join([_import_cleaned, item.rstrip()])
            else:
                #print("item found: %s" % item)
                pass
        _import_cleaned = _import_cleaned.lstrip(';')
        # remove password hash from export
        _export = _export.body.split(';')
        _export_cleaned = ''
        for item in _export:
            if not item.startswith('"$2a$10'):
                _export_cleaned = ';'.join([_export_cleaned, item.rstrip()])
            else:
                #print("item found: %s" % item)
                pass
        _export_cleaned = _export_cleaned.lstrip(';')

        # remove newline characters
        _ic = re.sub(r"\n", "", _import_cleaned)
        _ic = re.sub(r"\r", "", _ic)
        _ec = re.sub(r"\n", "", _export_cleaned)
        _ec = re.sub(r"\r", "", _ec)
        print("len(_ic): %s, _ic: %s" % (len(_ic), _ic))
        print("len(_ec): %s, _ec: %s" % (len(_ec), _ec))
        self.assertTrue(_ec in _ic)
        self.assertTrue(_ic in _ec)
