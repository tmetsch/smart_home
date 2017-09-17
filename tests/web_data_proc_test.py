"""
Unittests for the data proc module.
"""

import datetime
import logging
import os
import time
import threading
import unittest

import pandas as pd

from iot import sense
from web import data_proc

logging.basicConfig(level=logging.DEBUG)


class SensorFactoryTest(unittest.TestCase):
    """
    Testcase for SensorFactory class.
    """

    def setUp(self):
        sensor = DummySensor('testus', 'temp.db')
        sensor.start()
        sensor.join()

        self.cut = data_proc.SensorFactory('temp.db', '1Min')

    def tearDown(self):
        os.remove('temp.db')

    def test_get_sensors_for_success(self):
        """
        test for success.
        """
        self.cut.get_sensors()

    def test_get_sensors_for_failure(self):
        """
        test for failure.
        """
        pass  # N/A

    def test_get_sensors_for_sanity(self):
        """
        test for sanity.
        """
        tmp = self.cut.get_sensors()
        self.assertTrue(len(tmp), 1)
        self.assertEqual(tmp['testus'].name, 'testus')
        for item in tmp:
            self.assertIsInstance(tmp[item], data_proc.SensorData)


class SensorDataTest(unittest.TestCase):
    """
    Testcase for SensorData class.
    """

    def setUp(self):
        sensor = DummySensor('testus', 'temp.db')
        sensor.start()
        sensor.join()

        self.cut = data_proc.SensorFactory('temp.db',
                                           '1Min').get_sensors()['testus']

    def tearDown(self):
        os.remove('temp.db')

    def test_get_data_for_success(self):
        """
        test for success.
        """
        utcnow = datetime.datetime.utcnow()
        end = time.mktime(utcnow.timetuple())
        start = end - 60 * 10  # 10 mins.
        self.cut.get_data(start, end)

    def test_get_data_for_failure(self):
        """
        test for failure.
        """
        pass  # N/A

    def test_get_data_for_sanity(self):
        """
        test for sanity.
        """
        utcnow = datetime.datetime.utcnow()
        end = time.mktime(utcnow.timetuple())
        start = end - 2  # last 1 second

        data = self.cut.get_data(start, end)
        self.assertTrue(len(data) == 1)  # should be 1.

        start = end - 60 * 10  # last 10 mins.
        data = self.cut.get_data(start, end, resample=False)
        self.assertTrue(len(data) == 3)  # should have 3 datapoints.

        data = self.cut.get_data(start - 3600, end - 3600, resample=False)
        self.assertTrue(len(data) == 0)  # ask for range in the past


class GetDataTest(unittest.TestCase):
    """
    Test the get_data routine.
    """

    def setUp(self):
        tmp1 = {'temp': 10, 'hum': 12}
        tmp2 = {'pressure': 10}
        sensor1 = DummySensor('test1', 'temp.db', runtime=1, data=tmp1)
        sensor2 = DummySensor('test2', 'temp.db', runtime=1, data=tmp1)
        sensor3 = DummySensor('test3', 'temp.db', runtime=1, data=tmp2)

        threads = [sensor1, sensor2, sensor3]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.cut = data_proc.SensorFactory('temp.db', '1Min')

    def tearDown(self):
        os.remove('temp.db')

    def test_get_data_for_success(self):
        """
        Test for success.
        """
        utcnow = datetime.datetime.utcnow()
        end = time.mktime(utcnow.timetuple())
        start = end - 2  # last 1 second
        tmp = data_proc.get_data('temp.db', start, end, '1Min')
        self.assertIsNotNone(tmp)

    def test_get_data_for_failure(self):
        """
        Test for success.
        """
        pass  # TODO: implement.

    def test_get_data_for_sanity(self):
        """
        Test for success.
        """
        utcnow = datetime.datetime.utcnow()
        end = time.mktime(utcnow.timetuple())
        start = end - 2  # last 1 second
        tmp = data_proc.get_data('temp.db', start, end, '1Min')

        # get_data should group stuff together.
        self.assertTrue(len(tmp) == 3)  # 3 groups
        self.assertIn('temp', tmp)
        self.assertIn('hum', tmp)
        self.assertIn('pressure', tmp)

        self.assertIn('test1', tmp['temp'])
        self.assertIn('test2', tmp['temp'])
        self.assertIn('test1', tmp['hum'])
        self.assertIn('test2', tmp['hum'])
        self.assertIn('test3', tmp['pressure'])

        for item in tmp:
            self.assertIsInstance(tmp[item], pd.DataFrame)


class DummySensor(threading.Thread):
    """
    DummySensor inserting 1 datapoint.
    """

    def __init__(self, name, database, runtime=3, data=None):
        super(DummySensor, self).__init__()
        self.name = name
        self.database = database
        self.runtime = runtime
        if data is None:
            self.data = {'temperature': 23.0,
                         'humidity': 87.0}
        else:
            self.data = data

    def run(self):
        """
        Insert datapoints.
        """
        db_wrap = sense.DbWrapper(self.name, self.database)
        for _ in range(0, self.runtime):
            db_wrap.insert(datetime.datetime.utcnow(), self.data)
            time.sleep(1)
