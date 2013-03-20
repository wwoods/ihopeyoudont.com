import logging
import mock
import pymongo
import unittest

import app

class TestApp(unittest.TestCase):

    BASE_DATA = { 'from': 'fromv', 'email': 'emailv', 'action': 'actionv' }

    def setUp(self):
        self.app = app.app.test_client()
        self.db = pymongo.Connection()["ihopeyoudont_test"]
        self.db.connection.drop_database(self.db.name)
        app.c = self.db


    @mock.patch('app.send_mail', mock.Mock())
    def test_submit_logsToDb(self):
        r = self.app.post('/submit', data=self.BASE_DATA)
        self.assertEqual(1, app.send_mail.call_count)
        self.assertEqual(1, self.db['sent'].count())
        self.assertEqual(302, r.status_code)


    @mock.patch('app.send_mail', mock.Mock())
    def test_submit_longFields(self):
        for field in [ 'from', 'email', 'action' ]:
            logging.debug("For field '{}'".format(field))
            data = self.BASE_DATA.copy()
            data[field] = 'z' * 81
            app.send_mail.reset_mock()
            self.app.post('/submit', data = data)
            self.assertEqual(0, app.send_mail.call_count)


    @mock.patch('app.send_mail', mock.Mock())
    @mock.patch('app.throttleTest', mock.Mock(return_value = False))
    def test_submit_logsThrottle(self):
        self.app.post('/submit', data=self.BASE_DATA)
        self.assertEqual(1, self.db['throttling'].find_one()['count'])
        self.app.post('/submit', data=self.BASE_DATA)
        self.assertEqual(2, self.db['throttling'].find_one()['count'])
        self.assertEqual(0, app.send_mail.call_count)
