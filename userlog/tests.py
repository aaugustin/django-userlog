# coding: utf-8

from __future__ import unicode_literals

import os
import signal
import subprocess
import threading
import unittest

import django
from django.conf import settings
from django.contrib.auth.models import User
from selenium.webdriver.support import expected_conditions as ec

from . import util

try:
    import asyncio
except ImportError:
    asyncio = None
else:
    import websockets

try:
    from django.contrib.admin.tests import AdminSeleniumTestCase
except ImportError:
    from django.contrib.admin.tests import AdminSeleniumWebDriverTestCase \
        as AdminSeleniumTestCase


if asyncio:
    from . import realtime


class UserLogTestCaseBase(AdminSeleniumTestCase):

    available_apps = settings.INSTALLED_APPS
    browsers = ['firefox']

    @classmethod
    def setUpClass(cls):
        cls.redis = subprocess.Popen(
            ['redis-server', '--port', '0', '--unixsocket', 'redis.sock'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.environ['DJANGO_SELENIUM_TESTS'] = 'true'
        super(UserLogTestCaseBase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(UserLogTestCaseBase, cls).tearDownClass()

        cls.redis.send_signal(signal.SIGINT)
        cls.redis.wait()

    def tearDown(self):
        util.get_redis_client().flushdb()

    def search_username(self, username):
        self.selenium.find_element_by_name('username').send_keys(username)
        submit_xpath = '//input[@value="Rechercher"]'
        self.selenium.find_element_by_xpath(submit_xpath).click()

    def accept_alert(self, expected_text, timeout=1):
        self.wait_until(ec.alert_is_present(), timeout)
        alert = self.selenium.switch_to_alert()
        self.assertEqual(alert.text, expected_text)
        alert.accept()


class UserLogTestCase(UserLogTestCaseBase):

    def test_live_bigbrother(self):
        self.selenium.get(self.live_server_url + '/userlog/live/bigbrother/')
        self.accept_alert("Failed to connect. "
                          "Is the realtime endpoint running?")

    def test_live_logs(self):
        self.selenium.get(self.live_server_url + '/')

        link = self.selenium.find_element_by_css_selector('.model-live a')
        self.assertEqual(link.text, "Journaux dynamiques")
        link.click()

        self.search_username('admin')
        self.accept_alert("Failed to connect. "
                          "Is the realtime endpoint running?")
        self.wait_for_text('li.info', "Journal trouvé pour admin.")

        self.search_username('autre')
        self.wait_for_text('li.error', "Utilisateur autre non trouvé.")

        User.objects.create(username='autre')
        self.search_username('autre')
        self.accept_alert("Failed to connect. "
                          "Is the realtime endpoint running?")
        self.wait_for_text('li.info', "Journal trouvé pour autre.")

    def test_static_logs(self):
        self.selenium.get(self.live_server_url + '/')

        link = self.selenium.find_element_by_css_selector('.model-static a')
        self.assertEqual(link.text, "Journaux statiques")
        link.click()

        self.search_username('admin')
        self.wait_for_text('li.info', "Journal trouvé pour admin.")

        self.search_username('autre')
        self.wait_for_text('li.error', "Utilisateur autre non trouvé.")

        User.objects.create(username='autre')
        self.search_username('autre')
        self.wait_for_text('li.warning', "Pas de journal pour autre.")


@unittest.skipUnless(asyncio, "Live tests require Python ≥ 3.3 and asyncio.")
class UserLogRealTimeTestCase(UserLogTestCaseBase):

    # setUpClass & tearDownClass repeat code from UserLogTestCaseBase and
    # then call into AdminSeleniumTestCase because the shutdown sequence
    # must follow the dependency order: selenium -> websockets -> redis.

    @classmethod
    def setUpClass(cls):
        cls.redis = subprocess.Popen(
            ['redis-server', '--port', '0', '--unixsocket', 'redis.sock'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        cls.realtime_thread = threading.Thread(target=cls.run_realtime)
        cls.realtime_thread.start()

        os.environ['DJANGO_SELENIUM_TESTS'] = 'true'
        super(UserLogTestCaseBase, cls).setUpClass()        # call grand-parent

    @classmethod
    def run_realtime(cls):
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)  # required by asyncio_redis

        userlog_settings = util.get_userlog_settings()
        uri = websockets.parse_uri(userlog_settings.websocket_address)
        start_server = websockets.serve(
            realtime.userlog, uri.host, uri.port, loop=event_loop)

        stop_server = asyncio.Future(loop=event_loop)
        cls.stop_realtime_server = lambda: event_loop.call_soon_threadsafe(
            lambda: stop_server.set_result(True))

        realtime_server = event_loop.run_until_complete(start_server)
        event_loop.run_until_complete(stop_server)
        realtime_server.close()
        event_loop.run_until_complete(realtime_server.wait_closed())

        event_loop.close()

    @classmethod
    def tearDownClass(cls):
        super(UserLogTestCaseBase, cls).tearDownClass()     # call grand-parent

        cls.stop_realtime_server()
        cls.realtime_thread.join()

        cls.redis.send_signal(signal.SIGINT)
        cls.redis.wait()

    def test_live_bigbrother(self):
        self.selenium.get(self.live_server_url + '/userlog/live/bigbrother/')

        # This is an indirect way to wait for the websocket connection.
        user_heading = "Utilisateur"
        if django.VERSION >= (1, 9):
            user_heading = user_heading.upper()
        self.wait_for_text('table#result_list thead tr th:nth-child(1)',
                           user_heading)

        self.client.get('/non_existing/')

        self.wait_for_text('table#result_list tbody tr td:nth-child(1)',
                           "admin")
        self.wait_for_text('table#result_list tbody tr td:nth-child(3)',
                           "/non_existing/")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Lecture (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(5)',
                           "Erreur du client (404)")

    def test_live_logs(self):
        self.selenium.get(self.live_server_url + '/')

        link = self.selenium.find_element_by_css_selector('.model-live a')
        self.assertEqual(link.text, "Journaux dynamiques")
        link.click()

        self.search_username('admin')
        self.wait_for_text('li.info', "Journal trouvé pour admin.")

        self.wait_for_text('table#result_list tbody tr td:nth-child(2)',
                           "/userlog/live/")
        self.wait_for_text('table#result_list tbody tr td:nth-child(3)',
                           "Lecture (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Succès (200)")

        self.client.get('/non_existing/')
        self.wait_for_text('table#result_list tbody tr td:nth-child(2)',
                           "/non_existing/")
        self.wait_for_text('table#result_list tbody tr td:nth-child(3)',
                           "Lecture (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Erreur du client (404)")
