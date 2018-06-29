# coding: utf-8

'''Tests PypiPackageInfo.py.

See https://github.com/SublimeText/UnitTesting .
'''

import sys
import unittest
from unittest import mock

import requests


PypiPackageInfo = sys.modules['PypiPackageInfo.PypiPackageInfo']


@mock.patch.object(requests, 'get')
@mock.patch.object(PypiPackageInfo, 'PackageCache')
class TestPackageDataManager(unittest.TestCase):
    def setUp(self):
        self.dm = PypiPackageInfo.PackageDataManager()

    def test_get_data_cache_hit(self, PackageCache, get):
        instance = PackageCache.return_value
        instance.get_package_data.return_value = {'name': 'sample'}

        data = self.dm.get_data('sample')

        self.assertFalse(get.called)
        self.assertEquals(data['name'], 'sample')

    def test_get_data_response_not_ok(self, PackageCache, get):
        instance = PackageCache.return_value
        instance.get_package_data.return_value = False
        get.return_value.ok = False

        with self.assertRaises(PypiPackageInfo.CustomBaseException):
            self.dm.get_data('sample')

    def test_get_data_response_ok(self, PackageCache, get):
        instance = PackageCache.return_value
        instance.get_package_data.return_value = False
        get.return_value.ok = True
        get.return_value.json.return_value = {'name': 'sample'}

        data = self.dm.get_data('sample')

        self.assertTrue(get.called)
        self.assertIsInstance(data, dict)
        self.assertIn('name', data)
        self.assertNotIn('summary', data)
