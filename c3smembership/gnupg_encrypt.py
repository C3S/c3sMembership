#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module holds GnuPG functionality for c3sMembership.

GnuPG is used to encrypt email to staff

* when new applications for membership arrive
* for data export (e.g. CSV)
"""
#
# you need python-gnupg, so
# bin/pip install python-gnupg

import os
import gnupg
import tempfile
import shutil

DEBUG = False
# DEBUG = True


def encrypt_with_gnupg(data, keyid=""):
    """
    this function encrypts "data" with gnupg.

    returns strings:
    -----BEGIN PGP MESSAGE-----\n
    Version: GnuPG v1.4.11 (GNU/Linux)\n
    ...
    -----END PGP MESSAGE-----\n
    """
    keyfolder = tempfile.mkdtemp()

    assert keyid, "no gpg keyid specified"

    # TODO: check for a better way to do this:
    # do we really need to create a new tempdir for every run? no!
    # but hey as long as we need to run both as 'normal' user (while testing
    # on port 6544) and as www-data (apache) we do need separate folders,
    # because only the creator may access it.
    # however: as long as this is reasonably fast,
    # we can live with it. for now...

    gpg = gnupg.GPG(gnupghome=keyfolder)
    gpg.encoding = 'utf-8'

    # check if we have the membership key
    list_of_keys = gpg.list_keys()
    if DEBUG:  # pragma: no cover
        print(("=== the list of keys: " + repr(list_of_keys)))

    if keyid not in str(list_of_keys):
        # open and read key file
        # reading public key
        pubkey_content = None
        script_dir = os.path.dirname(os.path.realpath(__file__))
        keys_dir = os.path.join(script_dir, "..", "keys")
        for filename in os.listdir(keys_dir):
            if not filename.endswith(f"{keyid}.asc"):
                continue
            with open(os.path.join(keys_dir, filename)) as f:
                pubkey_content = "\n".join(f.readlines())
        assert pubkey_content, "no gpg key content found"
        # import public key
        gpg.import_keys(pubkey_content)
    else:
        if DEBUG:  # pragma: no cover
            print("=== not imported: key already known")
        pass

    if DEBUG:  # pragma: no cover
        print(("list_keys(): " + str(gpg.list_keys())))

    # prepare
    to_encode = data

    if isinstance(to_encode, str):
        to_encrypt = to_encode.encode(gpg.encoding)
    else:
        to_encrypt = to_encode

    if DEBUG:  # pragma: no cover
        print(("len(to_encrypt): " + str(len(str(to_encrypt)))))
        print(("encrypt_with_gnupg: type(to_encrypt): %s") % type(to_encrypt))

    # encrypt
    encrypted = gpg.encrypt(to_encrypt, keyid, always_trust=True)

    if DEBUG:  # pragma: no cover
        print(("encrypt_with_gnupg: type(encrypted): %s") % type(encrypted))
        print((
            "encrypt_with_gnupg: type(encrypted.data): %s"
        ) % type(
            encrypted.data))
        print("========================================== GNUPG END")
    shutil.rmtree(keyfolder)

    return encrypted.data


if __name__ == '__main__':  # pragma: no coverage

    my_unicode_text = """
    --                                      --
    --  So here is some sample text.        --
    --  With umlauts: öäß        --
    --  I want this to be encrypted.        --
    --  And then maybe send it via email    --
    --                                      --
    """
    result = encrypt_with_gnupg(
        my_unicode_text, 'A938D04BB2D9AAE1C1CCCA136B12C53270C76DD5')
    print(result)

    my_string = """
    --                                      --
    --  So here is some sample text.        --
    --  Without umlauts.                   --
    --  I want this to be encrypted.        --
    --  And then maybe send it via email    --
    --                                      --
    """
    result = encrypt_with_gnupg(
        my_string, 'A938D04BB2D9AAE1C1CCCA136B12C53270C76DD5')
    print(result)
