# -*- coding: utf-8 -*-
"""
Dues calculators to determine the dues amount of a member.
"""

from datetime import date

from decimal import Decimal


class DuesCalculator(object):
    """
    Abstract dues calculator base class
    """
    # pylint: disable=too-few-public-methods

    def calculate(self, member):
        """
        Calculates the dues for the member

        Args:
            member: The member for who the dues are calculated

        Returns:
            amount (Decimal): The amount of dues calculated.
            code (unicode): The code for the calculated dues.
            description (unicode): The description of the calculated dues.
        """
        raise NotImplementedError()


class QuarterlyDuesCalculator(object):
    """
    Calculator for quarterly dues for normal members

    Investing members do not pay any dues.
    """
    # pylint: disable=too-few-public-methods

    _DEFAULT_LOCALE = 'en'
    """Define the default locale for descriptions"""
    _QUARTERLY_FACTORS = {
        u'q1': Decimal('1'),
        u'q2': Decimal('0.75'),
        u'q3': Decimal('0.5'),
        u'q4': Decimal('0.25'),
    }
    """Define the quarterly factors for proportional dues amounts according to
    the quarters which have to be paid for"""
    _QUARTERLY_DESCRIPTIONS = {
        'en': {
            u'q1': u'whole year {year}',
            u'q2': u'from second quarter {year}',
            u'q3': u'from third quarter {year}',
            u'q4': u'from fourth quarter {year}',
        },
        'de': {
            u'q1': u'für das ganze Jahr {year}',
            u'q2': u'ab zweitem Quartal {year}',
            u'q3': u'ab drittem Quartal {year}',
            u'q4': u'ab viertem Quartal {year}',
        },
    }
    """Define the quarter descriptions for the locale"""

    def __init__(self, total_amount, year):
        """
        Initialise the QuarterlyDuesCalculator instance

        Args:
            total_amount: The total dues amount for the whole year
            year:  The year for which the dues is calculates

        Raises:
            TypeError: In case the parameter total_amount is not of type
                Decimal.
            TypeError: In case the parameter year is not of type int.
        """
        if not isinstance(total_amount, Decimal):
            raise TypeError('Parameter total_amount must be of type Decimal.')
        if not isinstance(year, int):
            raise TypeError('Parameter year must be of type int.')
        self._total_amount = total_amount
        self._year = year

    def calculate(self, member):
        """
        Calculates the quarterly dues for the member

        Members with a membership date:

        - before the beginning of the year and within the first quarter pay the
          full amount,
        - within the second quarter pay three fourth,
        - within the third quarter pay half,
        - within the fourth quarter pay one fourth of the total amount,
        - after the end of the year don't pay anything.

        Args:
            member: The member for who the quarterly dues are calculated

        Returns:
            amount (Decimal): The amount of quarterly dues calculated.
            code (unicode): The code for the calculated dues.
            description (unicode): The description of the calculated dues.
        """
        amount = Decimal('0.0')
        code = None
        description = None

        if member.membership_type == 'normal':
            quarter = self.calculate_quarter(member)
            if quarter is not None:
                quarterly_factor = self._QUARTERLY_FACTORS[quarter]
                amount = self._total_amount * quarterly_factor
                description = self.get_description(quarter, member.locale)
                code = u'{quarter}_{year}'.format(
                    quarter=quarter,
                    year=self._year)
        return (amount, code, description)

    def calculate_quarter(self, member):
        """
        Calculate the quarter for dues calculation

        Args:
            member: The member for who the quarter is calculated

        Returns:
            u'q1': For membership date until the end of March of the year
            u'q2': For membership date until the end of June of the year
            u'q3': For membership date until the end of September of the year
            u'q4': For membership date until the end of the year
            None: For membership date later than the end of the year
        """
        quarter = None
        if member.membership_date.year <= self._year:
            if member.membership_date < date(self._year, 4, 1):
                quarter = u'q1'
            elif member.membership_date < date(self._year, 7, 1):
                quarter = u'q2'
            elif member.membership_date < date(self._year, 10, 1):
                quarter = u'q3'
            elif member.membership_date >= date(self._year, 10, 1):
                quarter = u'q4'
        return quarter

    def get_description(self, quarter, member_locale):
        """
        Get the quarter description text for the given locale or default locale

        Args:
            quarter: The quarter of the year as u'q1', u'q2', u'q3' and u'q4'
            member_locale: The locale of the member

        Returns:
            The quarter description according to the member locale.
        """
        locale = self._DEFAULT_LOCALE
        if member_locale in self._QUARTERLY_DESCRIPTIONS:
            locale = member_locale
        return self._QUARTERLY_DESCRIPTIONS[locale][quarter].format(
            year=self._year)
