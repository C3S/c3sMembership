# -*- coding: utf-8 -*-

from unittest import TestCase
from c3smembership.presentation.pagination.property_naming import (
    ISortingPropertyNaming,
    IPagingPropertyNaming,
    IPropertyNaming,
    PropertyNaming
)


class TestISortingPropertyNaming(TestCase):

    def setUp(self):
        self._property_naming = ISortingPropertyNaming()

    def test_sort_property_name(self):
        with self.assertRaises(NotImplementedError):
            sort_property_name = self._property_naming.sort_property_name
            del(sort_property_name)

    def test_sort_direction_name(self):
        with self.assertRaises(NotImplementedError):
            sort_direction_name = self._property_naming.sort_direction_name
            del(sort_direction_name)


class TestIPagingPropertyNaming(TestCase):

    def setUp(self):
        self._property_naming = IPagingPropertyNaming()

    def test_page_number_name(self):
        with self.assertRaises(NotImplementedError):
            page_number_name = self._property_naming.page_number_name
            del(page_number_name)

    def test_page_size_name(self):
        with self.assertRaises(NotImplementedError):
            page_size_name = self._property_naming.page_size_name
            del(page_size_name)


class TestIPropertyNaming(TestCase):

    def setUp(self):
        self._property_naming = IPropertyNaming()

    def test_page_number_name(self):
        with self.assertRaises(NotImplementedError):
            page_number_name = self._property_naming.page_number_name
            del(page_number_name)

    def test_page_size_name(self):
        with self.assertRaises(NotImplementedError):
            page_size_name = self._property_naming.page_size_name
            del(page_size_name)

    def test_sort_property_name(self):
        with self.assertRaises(NotImplementedError):
            sort_property_name = self._property_naming.sort_property_name
            del(sort_property_name)

    def test_sort_direction_name(self):
        with self.assertRaises(NotImplementedError):
            sort_direction_name = self._property_naming.sort_direction_name
            del(sort_direction_name)


class TestPropertyNaming(TestCase):

    def setUp(self):
        self._default_format_property_naming = PropertyNaming(
            'page_number',
            'page_size',
            'sort_property',
            'sort_direction')
        self._prefix_property_naming = PropertyNaming(
            'page_number',
            'page_size',
            'sort_property',
            'sort_direction',
            'prefix.{property_name}')

    def test_page_number_name(self):
        self.assertEqual(
            self._default_format_property_naming.page_number_name,
            'page_number'
        )
        self.assertEqual(
            self._prefix_property_naming.page_number_name,
            'prefix.page_number'
        )

    def test_page_size_name(self):
        self.assertEqual(
            self._default_format_property_naming.page_size_name,
            'page_size'
        )
        self.assertEqual(
            self._prefix_property_naming.page_size_name,
            'prefix.page_size'
        )

    def test_sort_property_name(self):
        self.assertEqual(
            self._default_format_property_naming.sort_property_name,
            'sort_property'
        )
        self.assertEqual(
            self._prefix_property_naming.sort_property_name,
            'prefix.sort_property'
        )

    def test_sort_direction_name(self):
        self.assertEqual(
            self._default_format_property_naming.sort_direction_name,
            'sort_direction'
        )
        self.assertEqual(
            self._prefix_property_naming.sort_direction_name,
            'prefix.sort_direction'
        )
