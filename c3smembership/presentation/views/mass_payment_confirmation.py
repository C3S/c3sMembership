# -*- coding: utf-8 -*-
"""
This module holds functionality to handle mass payment confirmations.

Input is a reduced online banking export CSV.
"""

from c3smembership.data.model.base.c3smember import C3sMember
from c3smembership.data.model.base import DBSession
from decimal import Decimal
from io import StringIO
import datetime
import csv
import re

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config

from c3smembership.data.model.base import DBSession
from c3smembership.data.model.base.c3smember import C3sMember

DEBUG = False


@view_config(permission='manage',
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
    for row in reader:
        row_number = row_number + 1
        if len(row) != 5:
            request.session.flash(
                f"Expected exactly four values in line {row_number}."
                "Giving up.",
                'danger'
            )
            break        
        elif row_number == 1:
            """Ensure this looks like a valid reduced Hibiscus csv."""
            if (row[0] != "Datum" or
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
        else:  # process actual values
            # CSV fields
            csv_date = row[0]
            csv_name = row[1]
            csv_reference = row[2]
            csv_amount = row[3]
            csv_invoice_no = row[4]
            
            pattern = '^[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]$'
            if re.match(pattern, csv_invoice_no) is None:
                request.session.flash(
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} expected to match the "
                    "form 2345-6789. Manual confirmation necessary.",                                
                    'danger'
                )
                continue
            yy = csv_invoice_no[2:4]
            db_dues_invoice_no = getattr(C3sMember, f"dues{yy}_invoice_no")
            members = DBSession().query(C3sMember).where(db_dues_invoice_no                 
                == int(csv_invoice_no[5:]))
            if members.count() == 0:   # invoice code not found
                request.session.flash(
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} not found. "
                    "Manual confirmation necessary.",                        
                    'danger'
                )
                continue
            if members.count() > 1:  # obscure case
                request.session.flash(
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} found for more than one "
                    "member. This shouldn't occur. Please check db integrity!",                        
                    'danger'
                )
                continue
            member = members.one()

            # import debugpy
            # debugpy.listen(("0.0.0.0", 5253))
            # print("Waiting for debugger attach")
            # debugpy.wait_for_client()
            # debugpy.breakpoint()
            
            date = datetime.datetime.strptime(csv_date, "%d.%m.%Y")
            amount =  Decimal(csv_amount.replace(",", "."))
            
            # confirm payment
            db_dues_paid = getattr(member, f"dues{yy}_paid")
            db_dues_balance = getattr(member, f"dues{yy}_balance")
            set_dues_payment = getattr(member, f"set_dues{yy}_payment")
            if db_dues_paid:  # alread paid?
                request.session.flash(
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} was already paid. "
                    "Manual investigation necessary.",                        
                    'danger'
                )
                continue
            if db_dues_balance != Decimal(50) or amount != Decimal(50):
                request.session.flash(
                    f"Row number {row_number}: "
                    f"Invoice number {csv_invoice_no} mass confirmation "
                    "currently can only handle amounts and balances of 50 €. "
                    "Manual confirmation necessary.",                        
                    'danger'
                )
                continue
                
            set_dues_payment(amount, date)   
            request.session.flash(
                f"Row number {row_number}: "
                f"Invoice number {csv_invoice_no} confirmed. "
                f"'{csv_name}' --> '{member.firstname} {member.lastname}'",                
                'success'
            )         
    
    DBSession().flush()
    
    # response = Response(content_type='text/plain')
    # return response
    return HTTPFound(request.route_url('error'))  
