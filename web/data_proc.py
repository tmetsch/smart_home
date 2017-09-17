"""
Module taking care of the data processing.
"""

import logging
import sqlite3

import pandas as pd


class SensorFactory(object):
    """
    Factory for loading SensorData objects.
    """

    def __init__(self, database, resample):
        self.database = database
        self.resample = resample

    def get_sensors(self):
        """
        Return a list of objects that can be used to retrieve data per sensor.
        """
        res = {}
        conn = sqlite3.connect(self.database)
        tmp = conn.execute('SELECT name from sqlite_master WHERE type="table"')
        sensor_names = tmp.fetchall()
        logging.debug('Found following sensor information: ' +
                      repr(sensor_names))
        conn.close()

        for item in sensor_names:
            name = item[0]
            res[name] = SensorData(name, self.database, resample=self.resample)
        return res


class SensorData(object):
    """
    Wrapper for easy access to sensor data.
    """

    def __init__(self, table_name, database, resample):
        self.name = table_name
        self.conn = sqlite3.connect(database)
        self.resample = resample

    def get_data(self, start, end, resample=True, round=2):
        """
        Retrieve data over a time window bound by start and end.
        """
        # the column names
        tmp = 'pragma table_info({})'.format(self.name)
        res = self.conn.execute(tmp)
        columns = []
        for item in res.fetchall()[1:]:
            columns.append(item[1])  # name of the column

        # the values
        tmp = 'SELECT * FROM {} WHERE ' \
              'timestamp > {} AND timestamp <= {}'.format(self.name,
                                                          int(start),
                                                          int(end))
        dataframe = pd.read_sql_query(tmp, self.conn, index_col='timestamp')
        dataframe.index = pd.to_datetime(dataframe.index.values.astype(float),
                                         unit='s',
                                         utc=True)
        dataframe.sort_index(inplace=True)
        if resample:
            dataframe = dataframe.resample(self.resample).bfill()
        dataframe = dataframe.round(round)
        return dataframe


def get_data(database, start, end, sample_rate):
    """
    Retrieve data.
    """
    factory = SensorFactory(database, sample_rate)
    sensors = factory.get_sensors()

    res = {}

    for sensor in sensors:
        tmp = sensors[sensor].get_data(start, end)
        colums = set(sorted(tmp.columns.tolist()))
        for column in colums:
            s = tmp[column]
            if column not in res:
                res[column] = pd.DataFrame(s.tolist(),
                                           columns=[sensor],
                                           index=s.index)
            else:
                res[column] = pd.concat((res[column],
                                         s.rename(sensor)),
                                        axis=1,
                                        join='outer')
                pass

    for item in res:
        res[item].fillna(method='ffill')
        res[item].dropna(axis=0)

    return res
