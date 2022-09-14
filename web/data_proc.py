"""
Module taking care of the data processing.
"""

import logging
import sqlite3

import pandas as pd


class SensorFactory:
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
        logging.debug('Found following sensor information: %s',
                      repr(sensor_names))
        conn.close()

        for item in sensor_names:
            name = item[0]
            res[name] = SensorData(name, self.database, resample=self.resample)
        return res


class SensorData:
    """
    Wrapper for easy access to sensor data.
    """

    def __init__(self, table_name, database, resample):
        self.name = table_name
        self.conn = sqlite3.connect(database)
        self.resample = resample

    def get_data(self, start, end, resample=True, round_digits=2):
        """
        Retrieve data over a time window bound by start and end.
        """
        # the column names
        tmp = f'pragma table_info({self.name})'
        res = self.conn.execute(tmp)
        columns = []
        for item in res.fetchall()[1:]:
            columns.append(item[1])  # name of the column

        # the values
        tmp = f'SELECT * FROM {self.name} WHERE ' \
              f'timestamp > {int(start)} AND timestamp <= {int(end)}'
        dataframe = pd.read_sql_query(tmp, self.conn, index_col='timestamp')
        dataframe.index = pd.to_datetime(dataframe.index.values.astype(float),
                                         unit='s',
                                         utc=True)
        dataframe.sort_index(inplace=True)
        if resample:
            dataframe = dataframe.resample(self.resample).bfill()
        dataframe = dataframe.round(round_digits)
        return dataframe


def _calc_tau(row):
    if 'humidity' in row.keys() and 'temperature' in row.keys():
        hum = row['humidity']
        temp = row['temperature']
        return (hum / 100) ** (1 / 8.02) * (109.8 + temp) - 109.8
    else:
        return -1.0


def get_data(database, start, end, sample_rate):
    """
    Retrieve data.
    """
    factory = SensorFactory(database, sample_rate)
    sensors = factory.get_sensors()

    res = {}

    for key, item in sensors.items():
        tmp = item.get_data(start, end)
        tmp['tau'] = tmp.apply(lambda row: _calc_tau(row), axis=1)
        columns = list(sorted(tmp.columns.tolist()))
        for column in columns:
            series = tmp[column]
            if column not in res:
                res[column] = pd.DataFrame(series.tolist(),
                                           columns=[key],
                                           index=series.index)
            else:
                res[column] = pd.concat((res[column],
                                         series.rename(key)),
                                        axis=1,
                                        join='outer')

    for _, val in res.items():
        val.fillna(method='ffill', inplace=True)
        val.dropna(axis=0, inplace=True)

    return res
