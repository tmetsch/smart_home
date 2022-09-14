"""
Module containing all sensors.
"""

import datetime
import json
import http.client
import time
import threading
import traceback
import sqlite3

import logging

PI = True
try:
    import Adafruit_DHT
except ImportError:
    PI = False
    logging.error('GPIO not available...')


class DbWrapper:
    """
    Base sensor class - provides DB abstraction.
    """

    def __init__(self, name, database):
        self.name = name
        self.database = database

    def insert(self, timestamp, data):
        """
        Insert data into the database.

        Database assumes unique timestamp - and as we are working with int as
        timestamps this limits us to 1s sampling rate.
        """
        if not isinstance(timestamp, datetime.datetime):
            raise AttributeError('timestamp should be datetime tuple.')
        conn = sqlite3.connect(self.database)
        cur = conn.cursor()

        tmp = cur.execute(f'SELECT name from sqlite_master '
                          f'WHERE type="table" AND name="{self.name}"')

        # create table if needed.
        if len(tmp.fetchmany()) == 0:
            tmp = f'CREATE TABLE {self.name} (timestamp INTEGER'
            for item in data.keys():
                typo = 'TEXT'
                if isinstance(data[item], float):
                    typo = 'REAL'
                elif isinstance(data[item], int):
                    typo = 'INTEGER'
                tmp += f', {item} {typo}'
            tmp += ', CONSTRAINT ts_unique UNIQUE (timestamp) )'
            logging.debug('Creating table: %s.', repr(tmp))
            cur.execute(tmp)

        # insert data
        timestamp = time.mktime(timestamp.timetuple())

        tmp = f'INSERT INTO {self.name} VALUES ({timestamp}'
        for item in data.values():
            if isinstance(item, str):
                item = '"' + item + '"'
            tmp += f', {item}'
        tmp += ')'
        logging.debug('Adding data: %s.', repr(tmp))
        cur.execute(tmp)
        cur.close()

        conn.commit()


class DHT22Sensor(threading.Thread):
    """
    Grab sensor information from DHT.
    """

    def __init__(self, name, database, sleep=300, dht=22, gpio=14):
        super().__init__()
        self.name = name
        self.database = database
        self.stop = False

        # configs
        self.sleep = sleep
        self.dht = dht
        self.gpio = gpio

    def _get_values(self):
        # arg0 = dht version (22), arg1 = gpio pin
        humidity, temperature = Adafruit_DHT.read_retry(self.dht, self.gpio)
        if humidity is not None and temperature is not None:
            return temperature, humidity
        logging.warning('%s - values are -1.', self.name)
        return -1, -1

    def run(self):
        if PI:
            db_wrap = DbWrapper(self.name, self.database)
            while not self.stop:
                temp, humidity = self._get_values()
                if temp != -1 and humidity != -1:
                    timestamp = datetime.datetime.utcnow()
                    db_wrap.insert(timestamp,
                                   {'temperature': temp,
                                    'humidity': humidity})
                logging.debug(self.name + ' - values: ' +
                              repr([temp, humidity]))
                time.sleep(self.sleep)
        else:
            logging.warning('Adafruit N/A; or not running on pi...')


class OutdoorWeather(threading.Thread):
    """
    Grab information from online weather service.
    """

    def __init__(self, name, database, city_id, app_id, sleep=600):
        super().__init__()
        self.name = name
        self.database = database
        self.stop = False

        # configs
        self.sleep = sleep
        self.city_id = city_id
        self.app_id = app_id

    def _get_values(self):
        """
        return temp and humidity
        """
        temp = -1
        hum = -1
        try:
            conn = http.client.HTTPConnection('api.openweathermap.org')
            conn.request('GET',
                         f'/data/2.5/weather?id='
                         f'{self.city_id}&APPID={self.app_id}')
            result = conn.getresponse()

            if result.status == 200:
                data = result.read()
                data = json.loads(data)
                temp = float(data['main']['temp']) - 273.15
                hum = float(data['main']['humidity'])
        except:
            logging.warning('%s - values are -1.', self.name)
            traceback.print_exc()
        finally:
            conn.close()
        return temp, hum

    def run(self):
        db_wrap = DbWrapper(self.name, self.database)
        while not self.stop:
            temp, humidity = self._get_values()
            if temp != -1 and humidity != -1:
                timestamp = datetime.datetime.utcnow()
                db_wrap.insert(timestamp,
                               {'temperature': temp,
                                'humidity': humidity})
            logging.debug(self.name + ' - values: ' + repr([temp, humidity]))
            time.sleep(self.sleep)
