# -*- coding: utf-8 -*-

import os


def check_certificate_git_present():
    """
    helper function

    returns tuple(bool, string)
    depending on existence of file in certificate folder
    """
    certificate_git_path = os.path.join(
        os.path.dirname(__file__),
        '../../certificate')
    assert(os.path.isfile(
        os.path.join(certificate_git_path, "README.rst")))
    # assert(os.path.isfile(
    #     os.path.join(certificate_path, "urkunde_header_en.tex")))
    cert_git_not_present = os.path.isfile(
        os.path.join(certificate_git_path, "urkunde_header_en.tex"))
    reason = ("this installation of c3sMembership misses some files "
              "necessary for membership certificate creation.")
    print("*" * 75)
    print("Note: Skipping some tests "
          "because certificate git content not present.")
    print("*" * 75)
    return (cert_git_not_present, reason)
