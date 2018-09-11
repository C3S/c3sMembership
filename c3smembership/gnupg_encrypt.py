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
Version: GnuPG v2.0.22 (GNU/Linux)

mQENBFBIqlMBCADR7hxvDnwJkLgXU3Xol71eRkdNCAdIDnXQq/+Bmn5rxcJcXzNK
DyibSGbVVpwMMOIiVuKxM66QdlvBm+2/QUdD/kdcMTwRBFqP40N9T+vaIVDpit4r
6ZH1w8QD6EJTL0wbtmIkdAYMhYd0k4wDJ+xOcfx/VINiwhS5/DT38jimqmkaOEzs
DqzbBBogdZ+Tw+leC+D9JkSzGRjwO+UzUxjw4kdib9KbSppTbjv7HdL+Pn1y0ACd
2ELZjTumqQzQi19WFENNhMaRHlUU5iGp9sLbKUN0GtgxGYIs85QNXH/5/0Qr2ZjH
2/yZCyyWzZR0efut6WthcxFNb4OMDs056v5LABEBAAG0KUMzUyBZZXMhIChodHRw
Oi8vd3d3LmMzcy5jYykgPHllc0BjM3MuY2M+iQE4BBMBAgAiAhsDBgsJCAcDAgYV
CAIJCgsEFgIDAQIeAQIXgAUCW5epxAAKCRBx9rqRzdKBEDw/CAC5w8qR+EWfjtmo
fPwZYa3NPyMkI7rVfxmJwxGxj8lOjp0rQz99vXFvBkJf+Th287v+UnNERYCD5FkJ
GIM4qiFVz4wa3h/TzW1+C+tSUbBBOR573CbYFU65ybi5cU798EPepD7uePRQJBmf
RNFf0uwYa522YzL8TGFn4GILFGsulY/HhAvBQv3vIDlwgeAboAPiAsAoGTUKrcdb
12kqsvf6R3TCOxAjriE4Ue2Ls001o2pHYIG6rcp2fU79RFlzASEx+T3IU1hbR8Y8
VuosDRcKSfQYAb7JP+cXdQpym6nL5zeiG+NonLFGBPceVvJ1C4zttzNssf93yVsy
K8j8WggCuQENBFBIqlMBCACoys54nxs3nrRcUkwFG0lp3L8N0udCzckIiVgU/1Sd
gbfAD9rnRdKv4UE/uvn7MkfyO8V2V2OZANu8ZL+dtjmi6DWS2iTEXOl6Mn6j0Fyv
ZNDe6scvahPDjWYnrjOwrNy6FC5Y4eAyHTprABioZgfwNkonK5Oh0pXLRkr5z00l
HjnkxYwyoFoMa3T7j7sxS0t3bkYZxETMCd+5YqDyt7fPEZ2sPugi1oqVU/ytADNg
EpjkzUhl4iWYYkk8RlQ8MFWVWEJd34HO6iOT+Pz6A9anuRbEqYCWYlHxM3wBc2Kl
v/heN0yz5ldZVx1ug0/eLwexNecJOTpy2eQYjVLP/BwTABEBAAGJAR8EGAECAAkC
GwwFAluXqpkACgkQcfa6kc3SgRCl/wf9EPAvwXm8eabKeohq3Ml4JKeodA64LKAC
5xpcRGHpdYyduj4FMN+/cI5zBXRDWBKnspEX17nQ/boldXzQkWp/R64uyiD/cNu1
ynkmNIGFyNlEd5xNk5DUoEwjM8zmVF+bPSpGBy9Q/s6v8gsIT4TZ12SpxPbSCgIT
nZafeM6jnC2zs0duXsA9dSYV5jTQfeSYNbQEd7C4Mrl3Ix6mzCU5zQjS+3opUfbl
puHkdLPxW5Lv3YKaSTQZGMlIjwv1lK87+GYGWu3qU6ORn605xZizzDc1boKmGeGw
rzAF6HkMRirQuUkswGmDf46h5ecU+brT4BU8/JDVsiqX8mb94friQw==
=hLA3
-----END PGP PUBLIC KEY BLOCK-----"""
        # import public key
        gpg.import_keys(pubkey_content)
    else:
        if DEBUG:  # pragma: no cover
            print("=== not imported: key already known")
        pass

    if DEBUG:  # pragma: no cover
        print "list_keys(): " + str(gpg.list_keys())

    # prepare
    to_encode = data

    # if DEBUG:  # pragma: no cover
    #    print("encrypt_with_gnupg: data: %s") % data
    #    print("encrypt_with_gnupg: type(data): %s") % type(data)
    #    print("type of to_encode: %s") % type(to_encode)

    if isinstance(to_encode, unicode):
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
        print "len(to_encrypt): " + str(len(str(to_encrypt)))
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
        print ("========================================== GNUPG END")
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
    print result

    my_string = """
    --                                      --
    --  So here is some sample text.        --
    --  Without umlauts.                   --
    --  I want this to be encrypted.        --
    --  And then maybe send it via email    --
    --                                      --
    """
    result = encrypt_with_gnupg(my_string)
    print result
