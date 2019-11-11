#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
# import shutil
from pyramid import testing

from c3smembership.data.model.base import DBSession


def _initTestingDB():
    from c3smembership.scripts import initialize_db
    session = initialize_db.init()
    return session


class TestGnuPG(unittest.TestCase):
    """
    Test some utility functions used to interact with GnuPG.

    * encrypt some lines
    * encrypt some unicode lines (with umlauts)
    * import key
    """
    def setUp(self):
        self.config = testing.setUp()
        self.session = _initTestingDB()

    def tearDown(self):
        DBSession.remove()
        testing.tearDown()

    def test_encrypt_with_gnupg_w_umlauts(self):
        """
        test if unicode input is acceptable and digested
        """
        from c3smembership.gnupg_encrypt import encrypt_with_gnupg
        result = encrypt_with_gnupg(u'fuck the umläuts')
        self.assertTrue('-----BEGIN PGP MESSAGE-----' in str(result))
        self.assertTrue('-----END PGP MESSAGE-----' in str(result))

    def test_encrypt_with_gnupg_import_key(self):
        """
        test if encryption produces any result at all
        """
        from c3smembership.gnupg_encrypt import encrypt_with_gnupg
        result = encrypt_with_gnupg('foo')
        self.assertTrue('-----BEGIN PGP MESSAGE-----' in str(result))
        self.assertTrue('-----END PGP MESSAGE-----' in str(result))
