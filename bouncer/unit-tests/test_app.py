import tornado.web
from handlers import IndexHandler, URLInfoHandler
from tornado.testing import AsyncHTTPTestCase
import app
import json

class AppTest(AsyncHTTPTestCase):
    def get_app(self):
        return app.Application('../../config.ini')

    def test_positive(self):
        self.http_client.fetch(self.get_url('/urlinfo/1/www.t.pignhsdaih.com/ha?a=1&h=0'),
                self.stop)
        response = self.wait()
        res = json.loads(response.body)
        self.assertTrue(res['status'])

    def test_negative(self):
        self.http_client.fetch(self.get_url('/urlinfo/1/www.doesnotexit.com/no?d'),
                self.stop)
        response = self.wait()
        res = json.loads(response.body)
        self.assertFalse(res['status'])
