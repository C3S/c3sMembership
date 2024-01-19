# -*- coding: utf-8 -*-
"""
This module holds functionality to handle mass payment confirmations.

Input is a reduced online banking export CSV.
"""

from decimal import Decimal
from io import StringIO
import datetime
import csv
import re
from difflib import SequenceMatcher

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember

DEBUG = False


def check_for_comma(name):
    """
    'lastname, firstname' -> 'firstname lastname'
    """
    if name.find(',') == -1:
        return name
    else:
        name_splitted = name.split(',')
        name_reversed = name_splitted[::-1]
        name_joined = ' '.join(name_reversed)
        return name_joined.replace('  ', ' ')


@view_config(
    renderer='c3smembership.presentation:templates/pages/'
             'mass_payment_confirmation.pt',
    permission='manage',
    route_name='mass_payment_confirmation')
def mass_payment_confirmation(request):
    """
    Process payments and show results.
    """

    try:
        text_string = request.matchdict['text']
    except (KeyError, ValueError):
        request.session.flash(
            "Invalid CSV input.",
            'danger'
        )
        return HTTPFound(request.route_url('error'))

    f = StringIO(text_string)
    reader = csv.reader(f, delimiter=';', quoting=csv.QUOTE_ALL)
    row_number = 0
    outcome = []
    for row in reader:
        row_number = row_number + 1
        if len(row) != 5:
            request.session.flash(
                f"Expected exactly four values in line {row_number}."
                "Giving up.",
                'danger'
            )
            return HTTPFound(request.route_url('error'))
        if row_number == 1:
            # Ensure this looks like a valid reduced Hibiscus csv.
            if (
                    row[0] != "Datum" or
                    row[1] != "Gegenkonto Inhaber" or
                    row[2] != "Verwendungszwecke" or
                    row[3] != "Betrag" or
                    row[4] != "Rechnungscode"):
                request.session.flash(
                    "Expected CSV header line: \"Datum\";"
                    "\"Gegenkonto Inhaber\";\"Verwendungszwecke\";"
                    "\"Betrag\";\"Rechnungscode\""
                    "Giving up.",
                    'danger'
                )
                return HTTPFound(request.route_url('error'))
        else:  # process actual values
            # CSV fields
            csv_date = row[0]
            csv_name = check_for_comma(row[1])
            csv_reference = row[2]
            csv_amount = row[3]
            csv_invoice_no = row[4]

            outcome.append({
                'csv_date': csv_date,
                'csv_name': csv_name,
                'db_name': "",
                'db_name_color': "",
                'csv_reference': csv_reference,
                'csv_invoice_no': csv_invoice_no,
                'csv_amount': csv_amount,
                'db_dues_balance': Decimal(0),
                'db_dues_paid': None,
                'message': "",
                'member_id': -1,
                'success': False
            })
            pattern = '^[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]$'
            if re.match(pattern, csv_invoice_no) is None:
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} expected to match the "
                    "form 2345-6789. Manual confirmation necessary.")
                continue
            yy = csv_invoice_no[2:4]
            db_dues_invoice_no = getattr(C3sMember, f"dues{yy}_invoice_no")
            members = DBSession().query(C3sMember).where(
                db_dues_invoice_no == int(csv_invoice_no[5:]))
            if members.count() == 0:   # invoice code not found
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} not found. "
                    "Manual confirmation necessary."
                )
                continue
            if members.count() > 1:  # obscure case
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} found for more than one "
                    "member. This shouldn't occur. Please check db integrity!"
                )
                continue
            member = members.one()

            outcome[-1]['db_name'] = f'{member.firstname} {member.lastname}'
            db_name_lower = outcome[-1]['db_name'].lower()
            csv_name_lower = csv_name.lower()
            r = SequenceMatcher(None, db_name_lower, csv_name_lower).ratio()
            outcome[-1]['db_name_color'] = (
                '#%02X%02X%02X' % (256 - int(r*255), int(r*255), 0))
            date = datetime.datetime.strptime(csv_date, "%d.%m.%Y")
            amount = Decimal(csv_amount.replace(",", "."))
            outcome[-1]['member_id'] = member.id

            # confirm payment
            db_dues_paid = getattr(member, f"dues{yy}_paid")
            outcome[-1]['db_dues_paid'] = db_dues_paid
            db_dues_balance = getattr(member, f"dues{yy}_balance")
            outcome[-1]['db_dues_balance'] = db_dues_balance
            set_dues_payment = getattr(member, f"set_dues{yy}_payment")
            if db_dues_paid:  # already paid?
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} was already paid. "
                    "Manual investigation necessary."
                )
                continue
            if db_dues_balance != Decimal(50) or amount != Decimal(50):
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} mass confirmation "
                    "currently can only handle amounts and balances of 50 €. "
                    "Manual confirmation necessary. (Dues in db is set to "
                    f"{db_dues_balance}.)"
                )
                continue

            necessary_name_simularity = 80  # in %
            r_percent = int(r * 100)
            if r_percent < necessary_name_simularity:  # obscure case
                outcome[-1]['message'] = (
                    f"Row number {row_number}: "
                    f"Name similarity '{member.firstname} {member.lastname}' "
                    f"is only {r_percent}% and thus lower than the necessary "
                    f"similarity of {necessary_name_simularity}%. You need to "
                    'confirm the payment manually.'
                )
                continue

            outcome[-1]['success'] = True
            set_dues_payment(amount, date)
            outcome[-1]['message'] = (
                f"Row number {row_number}: "
                f"Invoice number {csv_invoice_no} confirmed. "
                f"'{csv_name}' --> '{member.firstname} {member.lastname}'"
            )

    DBSession().flush()

    return {
        'outcome': outcome,
        'row_count': row_number
    }
