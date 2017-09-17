"""
Main routines :)
"""

import logging

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from web import bottle_ssl
from web import wsgi_app


CFG = configparser.ConfigParser()
CFG.readfp(open('defaults.cfg'))

FORMAT = "%(asctime)s - %(filename)s - %(lineno)s - " \
         "%(levelname)s - %(message)s"
logging.basicConfig(format=FORMAT,
                    level=CFG.get('server', 'debug'))


def main():
    """
    Fire up web server.
    """
    app = wsgi_app.MainApp(CFG.get('data', 'database'),
                           CFG.getint('data', 'timeslice'),
                           CFG.get('data', 'resample'),
                           CFG.get('server', 'username'),
                           CFG.get('server', 'password')).app

    sec_app = bottle_ssl.get_app(app)
    serve = bottle_ssl.SecureServerAdapter(CFG.get('server', 'ssl_key'),
                                           CFG.get('server', 'ssl_cert'))
    serve.run(sec_app)


if __name__ == '__main__':
    main()
