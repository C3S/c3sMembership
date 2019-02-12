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
from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.tex_tools import TexTools

DEBUG = False


# How is the membership list reconstructed? By the processes only? This can
# involve changes of the firstname, lastname, address, membership status etc.

LATEX_HEADER = '''
\\input{{{header_file}}}
\\def\\numMembers{{{members_count}}}
\\def\\numShares{{{shares_count}}}
\\def\\sumShares{{{shares_value}}}
\\def\\today{{{effective_date}}}
\\input{{{footer_file}}}
'''

LATEX_FOOTER = '''
%\\end{tabular}%
\\end{longtable}%
\\label{LastPage}
\\end{document}
'''

LATEX_ADDRESS = '''
{address1_latex}
{address2_latex} \\linebreak
{postal_code_latex} {city} ({country_code})
'''

LATEX_MEMBER_ROW = '''
\\footnotesize {lastname} &
\\footnotesize {firstname} &
\\footnotesize {membership_number} &
\\scriptsize {address} &
\\footnotesize {membership_approval} &
\\footnotesize {membership_loss} &
\\footnotesize {shares} \\\\\\hline %
'''


def latex_address(address1, address2, postal_code, city, country_code):
    address2_latex = ''
    if len(address2) > 0:
        address2_latex = '\\linebreak '
        address2_latex += unicode(TexTools.escape(address2)).encode('utf-8')
    return LATEX_ADDRESS.format(
        address1_latex=unicode(TexTools.escape(address1)).encode('utf-8'),
        address2_latex=address2_latex,
        postal_code_latex=unicode(
            TexTools.escape(postal_code)).encode('utf-8'),
        city=unicode(TexTools.escape(city)).encode('utf-8'),
        country_code=unicode(TexTools.escape(country_code)).encode('utf-8'))


def latex_membership_loss(membership_loss_date, membership_loss_type):
    membership_loss = u''
    if membership_loss_date is not None:
        membership_loss += membership_loss_date.strftime('%d.%m.%Y')
    if membership_loss_type is not None:
        membership_loss += '\\linebreak '
        membership_loss += unicode(TexTools.escape(
            membership_loss_type)).encode('utf-8')
    return membership_loss


def generate_membership_list_pdf(effective_date, members):
    template_path = os.path.join(
        os.path.dirname(__file__),
        '../../../membership_list_pdflatex')
    latex_dir = tempfile.mkdtemp()
    latex_file = tempfile.NamedTemporaryFile(
        suffix='.tex',
        dir=latex_dir,
        delete=False,
    )

    shares_count = sum([member['shares_count'] for member in members])

    latex_file.write(
        LATEX_HEADER.format(
            header_file=os.path.abspath(
                os.path.join(
                    template_path,
                    'header')),
            footer_file=os.path.abspath(
                os.path.join(
                    template_path,
                    'footer')),
            members_count=len(members),
            shares_count=shares_count,
            shares_value=shares_count * 50,
            effective_date=effective_date.strftime('%d.%m.%Y'),
        ).encode('utf-8'))

    # make table rows per member
    for member in members:
        latex_file.write(
            LATEX_MEMBER_ROW.format(
                lastname=TexTools.escape(member['lastname']).encode('utf-8'),
                firstname=TexTools.escape(member['firstname']).encode('utf-8'),
                membership_number=TexTools.escape(
                    str(member['membership_number'])),
                address=latex_address(
                    member['address1'],
                    member['address2'],
                    member['postcode'],
                    member['city'],
                    member['country']),
                membership_approval=member['membership_date'].strftime(
                    '%d.%m.%Y'),
                membership_loss=latex_membership_loss(
                    member['membership_loss_date'],
                    member['membership_loss_type']),
                shares=str(member['shares_count'])))

    latex_file.write(LATEX_FOOTER)
    latex_file.close()

    # generate file three times in order to make sure all back references like
    # the number of total pages are properly calculated
    for i in range(3):
        subprocess.call(
            [
                'pdflatex',
                '-output-directory={0}'.format(latex_dir),
                latex_file.name
            ],
            stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT,
        )

    pdf_file = open(latex_file.name.replace('.tex', '.pdf'), "r")
    shutil.rmtree(latex_dir, ignore_errors=True)
    return pdf_file


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
            'danger'
        )
        return HTTPFound(request.route_url('error'))

    # TODO: repositories are data layer and must only be used by the business
    # layer. Introduce business layer logic which uses the repositories and can
    # be accessed by this view via the request.
    members = request.registry.member_information.get_accepted_members_sorted(
        effective_date)

    membership_list_entries = []
    for member in members:
        membership_list_entries.append({
            'lastname': member.lastname,
            'firstname': member.firstname,
            'membership_number': member.membership_number,
            'address1': member.address1,
            'address2': member.address2,
            'postcode': member.postcode,
            'city': member.city,
            'country': member.country,
            'membership_date': member.membership_date,
            'membership_loss_date': member.membership_loss_date,
            'membership_loss_type': member.membership_loss_type,
            'membership_number': member.membership_number,
            'shares_count': request.registry.share_information \
                .get_member_share_count(
                        member.membership_number,
                        effective_date)
        })

    response = Response(content_type='application/pdf')
    response.app_iter = generate_membership_list_pdf(
        effective_date,
        membership_list_entries)
    return response


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'membership_members_list.pt',
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
