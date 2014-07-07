# coding: utf-8

from __future__ import unicode_literals

try:
    import asyncio
except ImportError:
    asyncio = None
import os
import signal
import subprocess
import threading
import unittest

if asyncio:
    import websockets

from django.conf import settings
from django.contrib.admin.tests import AdminSeleniumWebDriverTestCase
from django.contrib.auth.models import User

from selenium.webdriver.support import expected_conditions as ec

if asyncio:
    from . import realtime
from . import util


class UserLogTestCase(AdminSeleniumWebDriverTestCase):

    available_apps = settings.INSTALLED_APPS

    @classmethod
    def setUpClass(cls):
        cls.redis = subprocess.Popen(
            ['redis-server', '--port', '0', '--unixsocket', 'redis.sock'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.environ['DJANGO_SELENIUM_TESTS'] = 'true'
        super(UserLogTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(UserLogTestCase, cls).tearDownClass()

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
class UserLogRealTimeTestCase(UserLogTestCase):

    # setUpClass & tearDownClass repeat code from UserLogTestCase and then
    # call into AdminSeleniumWebDriverTestCase because the shutdown sequence
    # must follow the dependency order: selenium -> websockets -> redis.

    @classmethod
    def setUpClass(cls):
        cls.redis = subprocess.Popen(
            ['redis-server', '--port', '0', '--unixsocket', 'redis.sock'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        cls.realtime_thread = threading.Thread(target=cls.run_realtime)
        cls.realtime_thread.start()

        os.environ['DJANGO_SELENIUM_TESTS'] = 'true'
        super(UserLogTestCase, cls).setUpClass()        # call grand-parent.

    @classmethod
    def run_realtime(cls):
        event_loop = asyncio.new_event_loop()
        cls.event_loop = event_loop
        asyncio.set_event_loop(event_loop)

        userlog_settings = util.get_userlog_settings()
        uri = websockets.parse_uri(userlog_settings.websocket_address)
        start_server = websockets.serve(realtime.userlog, uri.host, uri.port)
        cls.realtime_server = event_loop.run_until_complete(start_server)
        event_loop.run_until_complete(cls.realtime_server.wait_closed())
        event_loop.close()

    @classmethod
    def tearDownClass(cls):
        super(UserLogTestCase, cls).tearDownClass()     # call grand-parent.

        cls.event_loop.call_soon_threadsafe(cls.realtime_server.close)
        cls.realtime_thread.join()

        cls.redis.send_signal(signal.SIGINT)
        cls.redis.wait()

    def test_live_bigbrother(self):
        self.selenium.get(self.live_server_url + '/userlog/live/bigbrother/')

        self.client.get('/non_existing/')
        self.wait_for_text('table#result_list tbody tr td:nth-child(1)',
                           "admin")
        self.wait_for_text('table#result_list tbody tr td:nth-child(3)',
                           "/non_existing/")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Read (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(5)',
                           "Client error (404)")

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
                           "Read (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Success (200)")

        self.client.get('/non_existing/')
        self.wait_for_text('table#result_list tbody tr td:nth-child(2)',
                           "/non_existing/")
        self.wait_for_text('table#result_list tbody tr td:nth-child(3)',
                           "Read (GET)")
        self.wait_for_text('table#result_list tbody tr td:nth-child(4)',
                           "Client error (404)")

    def test_static_logs(self):
        return              # don't repeat test that doesn't involve realtime
