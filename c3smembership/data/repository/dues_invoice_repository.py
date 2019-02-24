# -*- coding: utf-8  -*-
"""
Repository for operating with dues invoices

The DuesInvoiceRepository is still being built up. It needs to abstract the
database structures from the business and presentation layers. Once this
abstraction is finalized the dues invoices data model can be changed to contain
all years in one table in order to not have to alter the data model for
following years.
"""

from c3smembership.data.model.base import (
    DBSession,
)
from c3smembership.data.model.base.dues15invoice import Dues15Invoice
from c3smembership.data.model.base.dues16invoice import Dues16Invoice
from c3smembership.data.model.base.dues17invoice import Dues17Invoice
from c3smembership.data.model.base.dues18invoice import Dues18Invoice
from c3smembership.data.model.base.dues19invoice import Dues19Invoice


class DuesInvoiceRepository(object):
    """
    Repository for operating with dues invoices
    """
    # pylint: disable=too-few-public-methods

    _DUES_INVOICE_CLASS = {
        2015: Dues15Invoice,
        2016: Dues16Invoice,
        2017: Dues17Invoice,
        2018: Dues18Invoice,
        2019: Dues19Invoice,
    }

    @classmethod
    def get_all(cls, years=None):
        """
        Get dues invoices

        If years is not specified then all available years are returned.

        Args:
            years (array): Defaults to None. An array of ints representing
                years.

        Returns:
            An array of dues invoices for the years specified.

        Example:
            dues_invoices = DuesInvoiceRepository.get_all([2015, 2018])
        """
        db_session = DBSession()
        result = []
        if years is None:
            years = []
            for year in cls._DUES_INVOICE_CLASS:
                years.append(year)
        for year in years:
            if year in cls._DUES_INVOICE_CLASS:
                result = result + db_session.query(
                    cls._DUES_INVOICE_CLASS[year]).all()
        return result

    @classmethod
    def get_by_number(cls, year, invoice_number):
        """
        Get the dues invoice by invoice number

        Args:
            year (int): The year to which the invoice number belongs
            invoice_number (int): The invoice number for the invoice to be
                retrieved

        Returns:
            The invoice having the invoice number for the specified year.
        """
        db_session = DBSession()
        result = None
        if year in cls._DUES_INVOICE_CLASS:
            result = db_session \
                .query(cls._DUES_INVOICE_CLASS[year]) \
                .filter(
                    cls._DUES_INVOICE_CLASS[year].invoice_no == invoice_number
                ) \
                .first()
        return result
