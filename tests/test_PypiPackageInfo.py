# coding: utf-8

'''Tests PypiPackageInfo.py.

See https://github.com/SublimeText/UnitTesting .
'''

import json
import os
import sqlite3
import sys
import tempfile
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


@mock.patch.object(PypiPackageInfo, 'CacheManager')
class TestPackageCache(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile()
        self.db_path = self.temp.name

    def test_init(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        PypiPackageInfo.PackageCache()

        row = self.get_db_table_count('packages')
        self.assertEquals(row[0], 1)

    def test_get_package_data_miss(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        pc = PypiPackageInfo.PackageCache()
        data = pc.get_package_data('sample')

        self.assertFalse(data)

    def test_get_package_data_hit(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        pc = PypiPackageInfo.PackageCache()
        with mock.patch.object(pc, 'conn') as conn:
            cur = conn.cursor.return_value
            cur.fetchone.return_value = {'data': json.dumps({'key': 'value'})}
            data = pc.get_package_data('sample')

        self.assertIsInstance(data, dict)
        self.assertEquals(data['key'], 'value')

    def test_add_package_data_data_added(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        pc = PypiPackageInfo.PackageCache()
        data = pc.get_package_data('AcmePackage')

        self.assertFalse(data)
        self.assertEquals(self.get_package_count(), 0)

        pc.add_package_data('AcmePackage', {
            'name': 'AcmePackage',
            'summary': 'This is an awesome package.',
        })

        self.assertEquals(self.get_package_count(), 1)

        data = pc.get_package_data('AcmePackage')

        self.assertIsInstance(data, dict)
        self.assertEquals(data['name'], 'AcmePackage')
        self.assertEquals(data['summary'], 'This is an awesome package.')

    def test_add_package_data_count_limited(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        pc = PypiPackageInfo.PackageCache()

        with mock.patch.object(pc, '_get_cache_max_count') as _get_cache_max_count:
            _get_cache_max_count.return_value = 30
            for i in range(100):
                pc.add_package_data('AcmePackage {}'.format(i), {})

        self.assertEquals(self.get_package_count(), 30)

    def test_clear_old_cache(self, CacheManager):
        self.use_temp_cache_manager(CacheManager, self.db_path)

        pc = PypiPackageInfo.PackageCache()

        self.assertEquals(self.get_package_count(), 0)

        for i in range(100):
            pc.add_package_data('AcmePackage {}'.format(i), {})

        self.assertEquals(self.get_package_count(), 100)

        with mock.patch.object(pc, '_get_cache_max_count') as _get_cache_max_count:
            _get_cache_max_count.return_value = 10
            pc.clear_old_cache()

        self.assertEquals(self.get_package_count(), 10)

    def test_clear_all_cache(self, CacheManager):
        temp = tempfile.NamedTemporaryFile(delete=False)
        db_path = temp.name

        self.use_temp_cache_manager(CacheManager, db_path)

        pc = PypiPackageInfo.PackageCache()
        pc.clear_all_cache()

        self.assertFalse(os.path.exists(db_path))

    def use_temp_cache_manager(self, CacheManager, path):
        cache_manager = CacheManager.return_value
        cache_manager.get_path.return_value = path

    def get_db_table_count(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'SELECT COUNT(name) FROM sqlite_master '
            "WHERE type='table' AND name=?",
            (table_name, ),
        )
        row = cur.fetchone()
        conn.close()
        return row

    def get_package_count(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM packages')
        row = cur.fetchone()
        conn.close()
        return row[0]
