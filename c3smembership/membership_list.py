# -*- coding: utf-8 -*-
"""
This module holds functionality to handle the C3S SCEs membership list.

Having and maintaining an alphabetical membership list is one of the
obligations of an association like the C3S SCE.

The list is available in several formats:

- HTML with clickable links for browsing
- HTML without links for printout
- PDF (created with pdflatex) for printout (preferred!)

There are also some historic utility functions for reference:

- Turn founders into members
- Turn crowdfunders into members
- Turn form users into members
- Flag duplicates
- Merge duplicates
"""
from datetime import (
    date,
    datetime,
)

import os
import shutil
import subprocess
import tempfile

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.models import (
    C3sMember,
)
from c3smembership.tex_tools import TexTools

DEBUG = False


# How is the membership list reconstructed? By the processes only? This can
# involve changes of the firstname, lastname, address, membership status etc.


@view_config(permission='manage',
             route_name='membership_listing_date_pdf')
def member_list_date_pdf_view(request):
    """
    The membership list *for a given date* for printout as PDF.
    The date is supplied in and parsed from the URL, e.g.
    http://0.0.0.0:6543/aml-2014-12-31.pdf

    The PDF is generated using pdflatex.

    If the date is not parseable, an error message is shown.
    """
    effective_date_string = ''
    try:
        effective_date_string = request.matchdict['date']
        effective_date = datetime.strptime(effective_date_string, '%Y-%m-%d') \
            .date()
    except (KeyError, ValueError):
        request.session.flash(
            "Invalid date! '{}' does not compute! "
            "try again, please! (YYYY-MM-DD)".format(
                effective_date_string),
            'message_to_user'
        )
        return HTTPFound(request.route_url('error_page'))

    shares_count_printed = 0

    # TODO: repositories are data layer and must only be used by the business
    # layer. Introduce business layer logic which uses the repositories and can
    # be accessed by this view via the request.
    shares_count = request.registry.share_information.get_share_count(
        effective_date)

    member_information = request.registry.member_information
    members_count = member_information.get_accepted_members_count(
        effective_date)
    members = member_information.get_accepted_members_sorted(
        effective_date)

    """
    Then a LaTeX file is constructed...
    """
    here = os.path.dirname(__file__)
    latex_header_tex = os.path.abspath(
        os.path.join(here, '../membership_list_pdflatex/header'))
    latex_footer_tex = os.path.abspath(
        os.path.join(here, '../membership_list_pdflatex/footer'))

    # a temporary directory for the latex run
    tempdir = tempfile.mkdtemp()
    # now we prepare a .tex file to be pdflatex'ed
    latex_file = tempfile.NamedTemporaryFile(
        suffix='.tex',
        dir=tempdir,
        delete=False,  # directory will be deleted anyways
    )
    # and where to store the output
    pdf_file = tempfile.NamedTemporaryFile(
        dir=tempdir,
        delete=False,  # directory will be deleted anyways
    )
    pdf_file.name = latex_file.name.replace('.tex', '.pdf')

    # construct latex data: header + variables
    latex_data = '''
\\input{%s}
\\def\\numMembers{%s}
\\def\\numShares{%s}
\\def\\sumShares{%s}
\\def\\today{%s}
    ''' % (
        latex_header_tex,
        members_count,
        shares_count,
        shares_count * 50,
        effective_date.strftime('%d.%m.%Y'),
    )

    # add to the latex document
    latex_data += '''
\\input{%s}''' % latex_footer_tex

    # print '*' * 70
    # print latex_data
    # print '*' * 70
    latex_file.write(latex_data.encode('utf-8'))

    # make table rows per member
    for member in members:
        address = '''\\scriptsize{}'''
        address += '''{}'''.format(
            unicode(TexTools.escape(member.address1)).encode('utf-8'))

        # check for contents of address2:
        if len(member.address2) > 0:
            address += '''\\linebreak {}'''.format(
                unicode(TexTools.escape(member.address2)).encode('utf-8'))
        # add more...
        address += ''' \\linebreak {} '''.format(
            unicode(TexTools.escape(member.postcode)).encode('utf-8'))
        address += '''{}'''.format(
            unicode(TexTools.escape(member.city)).encode('utf-8'))
        address += ''' ({})'''.format(
            unicode(TexTools.escape(member.country)).encode('utf-8'))

        member_share_count = \
            request.registry.share_information.get_member_share_count(
                member.membership_number,
                effective_date)
        shares_count_printed += member_share_count

        membership_loss = u''
        if member.membership_loss_date is not None:
            membership_loss += \
                member.membership_loss_date.strftime('%d.%m.%Y') + \
                '\\linebreak '
        if member.membership_loss_type is not None:
            membership_loss += unicode(TexTools.escape(
                member.membership_loss_type)).encode('utf-8')
        latex_file.write(
            ''' {0} & {1} & {2} & {3} & {4} & {5} & {6}  \\\\\\hline %
            '''.format(
                TexTools.escape(member.lastname).encode('utf-8'),  # 0
                ' \\footnotesize ' + TexTools.escape(
                    member.firstname).encode('utf-8'),  # 1
                ' \\footnotesize ' + TexTools.escape(
                    str(member.membership_number)),  # 2
                address,  # 3
                ' \\footnotesize ' + member.membership_date.strftime(
                    '%d.%m.%Y'),  # 4
                ' \\footnotesize ' + membership_loss + ' ',  # 5
                ' \\footnotesize ' + str(member_share_count)  # 6
            ))

    latex_file.write('''
%\\end{tabular}%
\\end{longtable}%
\\label{LastPage}
\\end{document}
''')
    latex_file.seek(0)  # rewind

    # pdflatex latex_file to pdf_file
    fnull = open(os.devnull, 'w')  # hide output
    pdflatex_output = subprocess.call(
        [
            'pdflatex',
            '-output-directory=%s' % tempdir,
            latex_file.name
        ],
        stdout=fnull, stderr=subprocess.STDOUT  # hide output
    )
    if DEBUG:  # pragma: no cover
        print("the output of pdflatex run: %s" % pdflatex_output)

    # if run was a success, run X times more...
    if pdflatex_output == 0:
        for i in range(2):
            pdflatex_output = subprocess.call(
                [
                    'pdflatex',
                    '-output-directory=%s' % tempdir,
                    latex_file.name
                ],
                stdout=fnull, stderr=subprocess.STDOUT  # hide output
            )
            if DEBUG:  # pragma: no cover
                print("run #{} finished.".format(i+1))

    # sanity check: did we print exactly as many shares as calculated?
    assert(shares_count == shares_count_printed)

    # return a pdf file
    response = Response(content_type='application/pdf')
    response.app_iter = open(pdf_file.name, "r")
    shutil.rmtree(tempdir, ignore_errors=True)  # delete temporary directory
    return response


@view_config(renderer='templates/member_list.pt',
             permission='manage',
             route_name='membership_listing_alphabetical')
def member_list_print_view(request):
    """
    This view produces printable HTML output, i.e. HTML without links

    It was used before the PDF-generating view above existed
    """
    all_members = C3sMember.member_listing(
        'lastname', how_many=C3sMember.get_number(), offset=0, order=u'asc')
    member_list = []
    count = 0
    for member in all_members:
        if member.is_member():
            # check membership number
            try:
                assert(member.membership_number is not None)
            except AssertionError:
                if DEBUG:  # pragma: no cover
                    print(u"failed at id {} lastname {}".format(
                        member.id, member.lastname))
            member_list.append(member)
            count += 1
    # sort members alphabetically
    import locale
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    member_list.sort(key=lambda x: x.firstname, cmp=locale.strcoll)
    member_list.sort(key=lambda x: x.lastname, cmp=locale.strcoll)

    return {
        'members': member_list,
        'count': count,
        '_today': date.today(),
    }


@view_config(permission='manage',
             route_name='merge_member')
def merge_member_view(request):
    """
    Merges member duplicates into one member record.

    Some people have more than one entry in our C3SMember table,
    e.g. because they used the application form more than once
    to acquire more shares.

    They shall not, however, become members twice and get more than one
    membership number. So we try and merge them:

    If a person is already a member and acquires a second package of shares,
    this package of shares is added to the former membership entry.
    The second entry in the C3sMember table is given the 'is_duplicate' flag
    and also the 'duplicate_of' is given the *id* of the original entry.
    """
    afm_id = request.matchdict['afm_id']
    member_id = request.matchdict['mid']
    if DEBUG:  # pragma: no cover
        print("shall merge {} to {}".format(afm_id, member_id))

    orig = C3sMember.get_by_id(member_id)
    merg = C3sMember.get_by_id(afm_id)

    if not orig.membership_accepted:
        request.session.flash(
            'you can only merge to accepted members!',
            'merge_message')
        HTTPFound(request.route_url('make_member', afm_id=afm_id))
    exceeds_60 = int(orig.num_shares) + int(merg.num_shares) > 60
    if exceeds_60:
        request.session.flash(
            'merger would exceed 60 shares!',
            'merge_message')
        return HTTPFound(request.route_url('make_member', afm_id=afm_id))

    # TODO: this needs fixing!!!
    # date must be set manually according to date of approval of the board
    shares_date_of_acquisition = merg.signature_received_date if (
        merg.signature_received_date > merg.payment_received_date
    ) else merg.payment_received_date

    share_acquisition = request.registry.share_acquisition
    share_id = share_acquisition.create(
        orig.membership_number,
        merg.num_shares,
        shares_date_of_acquisition)
    share_acquisition.set_signature_reception(
        share_id,
        date(
            merg.signature_received_date.year,
            merg.signature_received_date.month,
            merg.signature_received_date.day))
    share_acquisition.set_signature_confirmation(
        share_id,
        date(
            merg.signature_confirmed_date.year,
            merg.signature_confirmed_date.month,
            merg.signature_confirmed_date.day))
    share_acquisition.set_payment_reception(
        share_id,
        date(
            merg.payment_received_date.year,
            merg.payment_received_date.month,
            merg.payment_received_date.day))
    share_acquisition.set_payment_confirmation(
        share_id,
        date(
            merg.payment_confirmed_date.year,
            merg.payment_confirmed_date.month,
            merg.payment_confirmed_date.day))
    share_acquisition.set_reference_code(
        share_id,
        merg.email_confirm_code)

    DBSession.delete(merg)
    return HTTPFound(request.route_url('detail', memberid=member_id))


@view_config(renderer='templates/make_member.pt',
             permission='manage',
             route_name='make_member')
def make_member_view(request):
    """
    Turns a membership applicant into an accepted member.

    When both the signature and the payment for the shares have arrived at
    headquarters, an application for membership can be turned into an
    **accepted membership**, if the board of directors decides so.

    This view lets staff enter a date of approval through a form.

    It also provides staff with listings of

    * members with same first name
    * members with same last name
    * members with same email address
    * members with same date of birth

    so staff can decide if this may become a proper membership
    or whether this application is a duplicate of some accepted membership
    and should be merged with some other entry.

    In case of duplicate/merge, also check if the number of shares
    when combining both entries would exceed 60,
    the maximum number of shares a member can hold.
    """
    afm_id = request.matchdict['afm_id']
    try:  # does that id make sense? member exists?
        member = C3sMember.get_by_id(afm_id)
        assert(isinstance(member, C3sMember))  # is an application
        # not has number
    except AssertionError:
        return HTTPFound(
            location=request.route_url('dashboard'))
    if member.membership_accepted:
        # request.session.flash('id {} is already accepted member!')
        return HTTPFound(request.route_url('detail', memberid=member.id))

    if not (member.signature_received and member.payment_received):
        request.session.flash('signature or payment missing!', 'messages')
        return HTTPFound(request.route_url('dashboard'))

    if 'make_member' in request.POST:
        # print "yes! contents: {}".format(request.POST['make_member'])
        try:
            member.membership_date = datetime.strptime(
                request.POST['membership_date'], '%Y-%m-%d').date()
        except ValueError as value_error:
            request.session.flash(value_error.message, 'merge_message')
            return HTTPFound(
                request.route_url('make_member', afm_id=member.id))

        member.membership_accepted = True
        if member.is_legalentity:
            member.membership_type = u'investing'
        else:
            member.is_legalentity = False
        member.membership_number = C3sMember.get_next_free_membership_number()

        # Currently, the inconsistent data model stores the amount of applied
        # shares in member.num_shares which must be moved to a membership
        # application process property. As the acquisition of shares increases
        # the amount of shares and this is still read from member.num_shares,
        # this value must first be reset to 0 so that it can be increased by
        # the share acquisition. Once the new data model is complete the
        # property num_shares will not exist anymore. Instead, a membership
        # application process stores the number of applied shares and the
        # shares store the number of actual shares.
        num_shares = member.num_shares
        member.num_shares = 0

        share_id = request.registry.share_acquisition.create(
            member.membership_number,
            num_shares,
            member.membership_date)
        share_acquisition = request.registry.share_acquisition
        share_acquisition.set_signature_reception(
            share_id,
            date(
                member.signature_received_date.year,
                member.signature_received_date.month,
                member.signature_received_date.day))
        share_acquisition.set_payment_confirmation(
            share_id,
            date(
                member.payment_received_date.year,
                member.payment_received_date.month,
                member.payment_received_date.day))
        share_acquisition.set_reference_code(
            share_id,
            member.email_confirm_code)

        # return the user to the page she came from
        if 'referrer' in request.POST:
            if request.POST['referrer'] == 'dashboard':
                return HTTPFound(request.route_url('dashboard'))
            if request.POST['referrer'] == 'detail':
                return HTTPFound(
                    request.route_url('detail', memberid=member.id))
        return HTTPFound(request.route_url('detail', memberid=member.id))

    referrer = ''
    if 'dashboard' in request.referrer:
        referrer = 'dashboard'
    if 'detail' in request.referrer:
        referrer = 'detail'
    return {
        'member': member,
        'next_mship_number': C3sMember.get_next_free_membership_number(),
        'same_mships_firstn': C3sMember.get_same_firstnames(member.firstname),
        'same_mships_lastn': C3sMember.get_same_lastnames(member.lastname),
        'same_mships_email': C3sMember.get_same_email(member.email),
        'same_mships_dob': C3sMember.get_same_date_of_birth(
            member.date_of_birth),
        # keep information about the page the user came from in order to
        # return her to this page
        'referrer': referrer,
    }
