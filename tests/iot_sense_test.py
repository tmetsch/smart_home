"""
Unittest for sense module.
"""

import os
import sqlite3
import datetime
import unittest

from iot import sense


class DbWrapperTest(unittest.TestCase):
    """
    Test for class DbWrapper.
    """

    def setUp(self):
        self.cut = sense.DbWrapper('testus', 'temp.sqlite3')

    def tearDown(self):
        try:
            os.remove('temp.sqlite3')
        except OSError:
            # happens with test for failures.
            pass

    def test_insert_for_success(self):
        """
        Test for success.
        """
        self.cut.insert(datetime.datetime.now(), {'point1': 10.0})

    def test_insert_for_failure(self):
        """
        Test for failure.
        """
        # expects datetime obj
        self.assertRaises(AttributeError, self.cut.insert, 123, {})

    def test_insert_for_sanity(self):
        """
        Test for sanity.
        """
        now = datetime.datetime.now()
        self.cut.insert(now, {'metric1': 10.0,
                              'metric2': 'test',
                              'metric3': 1})
        cur = sqlite3.connect('temp.sqlite3')
        tmp = cur.execute('PRAGMA table_info(testus);')
        tmp = tmp.fetchall()

        self.assertEquals(tmp[0][2], 'INTEGER')  # timestamp
        self.assertEquals(tmp[1][2], 'INTEGER')  # metric3
        self.assertEquals(tmp[2][2], 'TEXT')  # metric2
        self.assertEquals(tmp[3][2], 'REAL')  # metric1
