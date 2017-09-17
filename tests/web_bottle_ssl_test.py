"""
Unittest for bottle SSL wrapper.
"""

import threading
import unittest

import bottle

from web import bottle_ssl


class SecureServerAdapterTest(unittest.TestCase):
    """
    Testcase for the SecureServerAdapter class.
    """

    def setUp(self):
        self.cut = bottle_ssl.SecureServerAdapter('tests/files/key.pem',
                                                  'tests/files/cert.pem')
        self.app = bottle.app

    def test_run_for_success(self):
        """
        Test for success.
        """
        thread = threading.Thread(target=self.cut.run, args=self.app)
        thread.setDaemon(True)
        thread.start()

    def test_run_for_failure(self):
        """
        Test for failure.
        """
        pass  # N/A

    def test_run_for_sanity(self):
        """
        Test for sanity.
        """
        pass  # TODO: implement
