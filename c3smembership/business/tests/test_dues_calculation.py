# -*- coding: utf-8 -*-
"""
Test the c3smembership.business.dues_calculation module
"""

from datetime import date
from decimal import Decimal
from unittest import TestCase

import mock

from c3smembership.business.dues_calculation import (
    DuesCalculator,
    QuarterlyDuesCalculator,
)


class DuesCalculatorTest(TestCase):
    """
    Test the abstract dues calculator base class
    """

    def test_calculate(self):
        """
        Test the calculate method
        """
        calculator = DuesCalculator()
        with self.assertRaises(NotImplementedError):
            calculator.calculate(None)


class QuarterlyDuesCalculatorTest(TestCase):
    """
    Test the QuarterlyDuesCalculator class
    """

    def test_calculate_quarters(self):
        """
        Test the calculate method

        1. Test quarter 1
        2. Test quarter 2
        3. Test quarter 3
        4. Test quarter 4
        """
        # pylint: disable=too-many-statements
        calculator = QuarterlyDuesCalculator(Decimal('50.0'), 2016)

        # 1. Test quarter 1
        member = mock.Mock()
        member.membership_date = date(2015, 12, 31)
        member.locale = 'en'
        member.membership_type = 'normal'

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('50.0'))
        self.assertEqual(dues_calculation.code, u'q1_2016')

        member.membership_date = date(2016, 1, 1)
        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('50.0'))
        self.assertEqual(dues_calculation.code, u'q1_2016')

        member.membership_date = date(2016, 3, 31)
        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('50.0'))
        self.assertEqual(dues_calculation.code, u'q1_2016')

        # 2. Test quarter 2
        member = mock.Mock()
        member.locale = 'en'
        member.membership_type = 'normal'
        member.membership_date = date(2016, 4, 1)

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('37.5'))
        self.assertEqual(dues_calculation.code, u'q2_2016')

        member.membership_date = date(2016, 6, 30)
        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('37.5'))
        self.assertEqual(dues_calculation.code, u'q2_2016')

        # 3. Test quarter 3
        member = mock.Mock()
        member.locale = 'en'
        member.membership_type = 'normal'
        member.membership_date = date(2016, 7, 1)

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('25.0'))
        self.assertEqual(dues_calculation.code, u'q3_2016')

        member.membership_date = date(2016, 9, 30)
        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('25.0'))
        self.assertEqual(dues_calculation.code, u'q3_2016')

        # 4. Test quarter 4
        member = mock.Mock()
        member.locale = 'en'
        member.membership_type = 'normal'
        member.membership_date = date(2016, 10, 1)

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('12.5'))
        self.assertEqual(dues_calculation.code, u'q4_2016')

        member.membership_date = date(2016, 12, 31)
        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('12.5'))
        self.assertEqual(dues_calculation.code, u'q4_2016')

    def test_calculate_after_the_year(self):
        """
        Test the calculate method for membership dates after the dues year
        """
        calculator = QuarterlyDuesCalculator(Decimal('50.0'), 2016)
        member = mock.Mock()
        member.locale = 'en'
        member.membership_type = 'normal'
        member.membership_date = date(2017, 1, 1)

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('0.0'))
        self.assertIsNone(dues_calculation.code)

    def test_calculate_validation(self):
        """
        Test the calculate method for type validation
        """
        with self.assertRaises(TypeError) as raise_context:
            QuarterlyDuesCalculator(None, 2018)
        self.assertTrue('total_amount' in str(raise_context.exception))
        with self.assertRaises(TypeError) as raise_context:
            QuarterlyDuesCalculator(Decimal('0.0'), None)
        self.assertTrue('year' in str(raise_context.exception))

    def test_calculate_locale(self):
        """
        Test the calculate method for different locale
        """
        calculator = QuarterlyDuesCalculator(Decimal('50.0'), 2016)
        member = mock.Mock()
        member.membership_type = 'normal'
        member.membership_date = date(2015, 12, 31)
        member.locale = 'de'

        dues_calculation = calculator.calculate(member)
        self.assertEqual(dues_calculation.amount, Decimal('50.0'))
        self.assertEqual(dues_calculation.code, u'q1_2016')

    def test_get_description(self):
        """
        Test the get_description method
        """
        calculator = QuarterlyDuesCalculator(Decimal('50.0'), 2016)

        # Test English local
        description = calculator.get_description(u'q1', 'en')
        self.assertEqual(description, u'whole year 2016')
        description = calculator.get_description(u'q2', 'en')
        self.assertEqual(description, u'from second quarter 2016')
        description = calculator.get_description(u'q3', 'en')
        self.assertEqual(description, u'from third quarter 2016')
        description = calculator.get_description(u'q4', 'en')
        self.assertEqual(description, u'from fourth quarter 2016')

        # Test German local
        description = calculator.get_description(u'q1', 'de')
        self.assertEqual(description, u'für das ganze Jahr 2016')
        description = calculator.get_description(u'q2', 'de')
        self.assertEqual(description, u'ab zweitem Quartal 2016')
        description = calculator.get_description(u'q3', 'de')
        self.assertEqual(description, u'ab drittem Quartal 2016')
        description = calculator.get_description(u'q4', 'de')
        self.assertEqual(description, u'ab viertem Quartal 2016')

        # Test default locale
        description = calculator.get_description(u'q1', 'xy')
        self.assertEqual(description, u'whole year 2016')
        description = calculator.get_description(u'q2', 'xy')
        self.assertEqual(description, u'from second quarter 2016')
        description = calculator.get_description(u'q3', 'xy')
        self.assertEqual(description, u'from third quarter 2016')
        description = calculator.get_description(u'q4', 'xy')
        self.assertEqual(description, u'from fourth quarter 2016')
