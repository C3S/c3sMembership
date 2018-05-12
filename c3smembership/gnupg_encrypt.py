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

import gnupg
import tempfile
import shutil

from c3smembership import unicode

DEBUG = False
# DEBUG = True


def encrypt_with_gnupg(data):
    """
    this function encrypts "data" with gnupg.

    returns strings:
    -----BEGIN PGP MESSAGE-----\n
    Version: GnuPG v1.4.11 (GNU/Linux)\n
    ...
    -----END PGP MESSAGE-----\n
    """
    # we use a folder named 'keys' to store stuff

    # if os.path.exists("keys"):
    #     if DEBUG:  # pragma: no cover
    #         print("===================================== GNUPG START")
    #         print "folder 'keys' exists"
    #     shutil.rmtree("keys")     # delete to renew
    #     print "deleted keys"

    # tempfile approach
    keyfolder = tempfile.mkdtemp()
    # print(keyfolder)

    # TODO: check for a better way to do this:
    # do we really need to create a new tempdir for every run? no!
    # but hey as long as we need to run both as 'normal' user (while testing
    # on port 6544) and as www-data (apache) we do need separate folders,
    # because only the creator may access it.
    # however: as long as this is reasonably fast,
    # we can live with it. for now...

    #    if DEBUG:  # pragma: no cover
    #        # a gpg object to work with
    #        gpg = gnupg.GPG(gnupghome="keys", verbose=True)
    #    else:
    # gpg = gnupg.GPG(gnupghome="keys")
    gpg = gnupg.GPG(gnupghome=keyfolder)
    gpg.encoding = 'utf-8'

    # check if we have the membership key
    list_of_keys = gpg.list_keys()
    if DEBUG:  # pragma: no cover
        print("=== the list of keys: " + repr(list_of_keys))

    if 'C3S-Yes!' not in str(list_of_keys):
        # open and read key file
        # reading public key
        pubkey_content = """
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2

mQENBFBIqlMBCADR7hxvDnwJkLgXU3Xol71eRkdNCAdIDnXQq/+Bmn5rxcJcXzNK
DyibSGbVVpwMMOIiVuKxM66QdlvBm+2/QUdD/kdcMTwRBFqP40N9T+vaIVDpit4r
6ZH1w8QD6EJTL0wbtmIkdAYMhYd0k4wDJ+xOcfx/VINiwhS5/DT38jimqmkaOEzs
DqzbBBogdZ+Tw+leC+D9JkSzGRjwO+UzUxjw4kdib9KbSppTbjv7HdL+Pn1y0ACd
2ELZjTumqQzQi19WFENNhMaRHlUU5iGp9sLbKUN0GtgxGYIs85QNXH/5/0Qr2ZjH
2/yZCyyWzZR0efut6WthcxFNb4OMDs056v5LABEBAAG0KUMzUyBZZXMhIChodHRw
Oi8vd3d3LmMzcy5jYykgPHllc0BjM3MuY2M+iQE+BBMBCgAoAhsDBgsJCAcDAgYV
CAIJCgsEFgIDAQIeAQIXgAUCV83LfAUJC0jZqQAKCRBx9rqRzdKBEACkB/9kAELG
KiIwOhMK2s+/Qlns/2Yfd53GxvnUyh4AAHI0kO9Y+5ULuaxnTPKaar5piYQHxN20
ewyPB5h+iiQC/lOf/l57HYGIEJYTmld5a+lU4kzEfL3JHBWor4lLBWiTU95ShOLs
AkOaxYmSDGVh8OmUL8NN/OL8FMhp6A8jrtVfs+TwLTV6uH/GuswIpR2q81I1Ef7m
ersSCwHGGNB+LeBvJLkOphlXZ8+l+YvzkK0xD/E4G5eDFpts5SqIQqDDKI62I4eM
8o3cefPf9PXNnaj6WMD2Tz4nIZysavDpSqBDNpxrX20c0ziT4EeBSJsOmuKmNrQr
cCEtHvaD9/3SqXM2uQENBFBIqlMBCACoys54nxs3nrRcUkwFG0lp3L8N0udCzckI
iVgU/1SdgbfAD9rnRdKv4UE/uvn7MkfyO8V2V2OZANu8ZL+dtjmi6DWS2iTEXOl6
Mn6j0FyvZNDe6scvahPDjWYnrjOwrNy6FC5Y4eAyHTprABioZgfwNkonK5Oh0pXL
Rkr5z00lHjnkxYwyoFoMa3T7j7sxS0t3bkYZxETMCd+5YqDyt7fPEZ2sPugi1oqV
U/ytADNgEpjkzUhl4iWYYkk8RlQ8MFWVWEJd34HO6iOT+Pz6A9anuRbEqYCWYlHx
M3wBc2Klv/heN0yz5ldZVx1ug0/eLwexNecJOTpy2eQYjVLP/BwTABEBAAGJASUE
GAEKAA8CGwwFAlfNy8YFCQtHiHMACgkQcfa6kc3SgRCCWAf/f2MgEzQ4+raN5otg
zJBj9v3vBv1oZHFCFfIsqALnhyRjPIkyGJJe6scH+2NqDNaK1KgImQf0c4pw/k9x
KFE01Y5v20ob8GRWd6/8iYKUUpd8Jj73P01RcJgVqOWaRwPnAG7sWpruVz7FmbuE
dIXH7Z6+h8NRWpjWrWaQtR4bzknYPBBQloe4I6sKwKKIliiEbEyzF/aCfG4hFtLB
tmmIVDVAu4dqq5cYhwX3q4ZZEfloM12g1otVRHONJ5FwowVHZgW1n8XPRFGDRa8F
iRxv2JwkwRYtQFg5bFO3NqulcEBAgSmz/TViRvGS3xBZtu08jUW55k9EIuAKzJ3K
43oF7w==
=vq3Z
-----END PGP PUBLIC KEY BLOCK-----
"""
        # import public key
        gpg.import_keys(pubkey_content)
    else:
        if DEBUG:  # pragma: no cover
            print("=== not imported: key already known")
        pass

    if DEBUG:  # pragma: no cover
        print("list_keys(): " + str(gpg.list_keys()))

    # prepare
    to_encode = data

    # if DEBUG:  # pragma: no cover
    #    print("encrypt_with_gnupg: data: %s") % data
    #    print("encrypt_with_gnupg: type(data): %s") % type(data)
    #    print("type of to_encode: %s") % type(to_encode)

    if type(to_encode) == unicode:
        # print("type is unicode")
        to_encrypt = to_encode.encode(gpg.encoding)
    else:
        to_encrypt = to_encode
    # elif isinstance(to_encode, str):
    #    print("type was string")
    #    to_encrypt = to_encode.encode(gpg.encoding)
    #    print("type is now %s") % type(to_encrypt)
    # else:
    #    print("type is neither str nor unicode: %s") % type(to_encode)

    if DEBUG:  # pragma: no cover
        print("len(to_encrypt): " + str(len(str(to_encrypt))))
        # print("encrypt_with_gnupg: to_encrypt: %s") % to_encrypt
        print("encrypt_with_gnupg: type(to_encrypt): %s") % type(to_encrypt)

    # encrypt
    encrypted = gpg.encrypt(
        to_encrypt,
        '89FC70ECCAD4487972D8924D71F6BA91CDD28110',  # key fingerprint
        # 'ED6CAAC657A45BCF55EAE6EFE83C7CFC7CB6F90F',  # key fingerprint
        always_trust=True)

    if DEBUG:  # pragma: no cover
        # print("encrypt_with_gnupg: encrypted: %s") % encrypted
        print("encrypt_with_gnupg: type(encrypted): %s") % type(encrypted)
        print(
            "encrypt_with_gnupg: type(encrypted.data): %s"
        ) % type(
            encrypted.data)
        # print "encrypted: " + str(encrypted)
        # print "len(encrypted): " + str(len(str(encrypted)))
        print("========================================== GNUPG END")
    shutil.rmtree(keyfolder)

    return encrypted.data


if __name__ == '__main__':  # pragma: no coverage

    my_unicode_text = u"""
    --                                      --
    --  So here is some sample text.        --
    --  With umlauts: öäß        --
    --  I want this to be encrypted.        --
    --  And then maybe send it via email    --
    --                                      --
    """
    result = encrypt_with_gnupg(my_unicode_text)
    print(result)

    my_string = """
    --                                      --
    --  So here is some sample text.        --
    --  Without umlauts.                   --
    --  I want this to be encrypted.        --
    --  And then maybe send it via email    --
    --                                      --
    """
    result = encrypt_with_gnupg(my_string)
    print(result)
