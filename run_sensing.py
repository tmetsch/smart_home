"""
Run a bunch of sensors.
"""

import logging

try:
    import ConfigParser as configparser
except ImportError:
    import configparser


from iot import sense

CFG = configparser.ConfigParser()
CFG.readfp(open('defaults.cfg'))

FORMAT = "%(asctime)s - %(filename)s - %(lineno)s - " \
         "%(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT,
                    level=CFG.get('server', 'debug'))


def main():
    """
    Start sensors as threads.
    """
    sensor1 = sense.OutdoorWeather('outdoor',
                                   CFG.get('data', 'database'),
                                   CFG.get('outdoor_sensor', 'city_id'),
                                   CFG.get('outdoor_sensor', 'app_id'),
                                   CFG.getint('outdoor_sensor', 'sleep'))
    sensor2 = sense.DHT22Sensor('indoor',
                                CFG.get('data', 'database'),
                                CFG.getint('indoor_sensor', 'sleep'),
                                CFG.getint('indoor_sensor', 'dht'),
                                CFG.getint('indoor_sensor', 'gpio'))
    threads = [sensor1, sensor2]

    for thread in threads:
        thread.start()


if __name__ == '__main__':
    main()
