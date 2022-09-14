"""
WSGI app.
"""

import datetime
import os
import time

import bottle

from web import data_proc

PASSPHRASE = os.urandom(2048)


class MainApp:
    """
    The main WSGI web app.
    """

    def __init__(self, database, timeslice, sample_rate, user, passwd):
        self.app = bottle.Bottle()
        self.database = database
        self.timeslice = timeslice
        self.sample_rate = sample_rate
        self.user = user
        self.passwd = passwd

        self._route()

    def _route(self):
        """
        Setup routes.
        """
        self.app.route('/', method="GET", callback=self._index_page)
        self.app.route('/login', callback=self._login)
        self.app.route('/login', callback=self._do_login, method='POST')
        self.app.route('/static/<filename:path>', callback=self._static)
        # TODO: add download
        # TODO: add statistics.

    def _check_login(self, user, pwd):
        # FIXME: poor approach.
        return user == self.user and pwd == self.passwd

    @bottle.view('login.tmpl')
    def _login(self):
        return None

    def _do_login(self):
        username = bottle.request.forms.get('username')
        password = bottle.request.forms.get('password')
        if self._check_login(username, password):
            bottle.response.set_cookie("account", username, secret=PASSPHRASE)
            bottle.redirect("/")
        else:
            return "<p>Login failed.</p>"

    @bottle.view('index.tmpl')
    def _index_page(self):
        username = bottle.request.get_cookie("account", secret=PASSPHRASE)
        if username:
            # FIXME: add more colors here :-)
            colors = ['#95b143', '#444', '#95b143', '#444']

            utcnow = datetime.datetime.utcnow()
            end = time.mktime(utcnow.timetuple())
            start = end - self.timeslice

            data = data_proc.get_data(self.database,
                                      start,
                                      end,
                                      self.sample_rate)

            titles = []
            datasets = {}
            for key, val in data.items():
                titles.append(key)
                temp = val
                data1 = {'labels': [str(x) for x in
                                    temp.index.strftime('%H:%M:%S').tolist()],
                         'datasets': []}
                i = 0
                for column in list(temp):
                    series = {'label': str(column),
                              'data': temp[column].tolist(),
                              'fill': 'false',
                              'borderColor': colors[i]}
                    data1['datasets'].append(series)
                    i += 1
                datasets[key] = data1

            return {'titles': titles,
                    'datasets': datasets,
                    'time': str(datetime.datetime.fromtimestamp(end))}
        return bottle.redirect("/login")

    def _static(self, filename):
        username = bottle.request.get_cookie("account", secret=PASSPHRASE)
        if username:
            return bottle.static_file(filename, root='views/static/')
        elif filename == 'style.css':
            return bottle.static_file(filename, root='views/static/')
        return bottle.redirect("/login")
