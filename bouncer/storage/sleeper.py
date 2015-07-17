from . import VerdictDB
from tornado import gen
from tornado.concurrent import Future
import random
import time
import logging

"""
This class just sleeps for a configured time and randomly
 returns a verdict based on configured probability. Useful for testing delays.
"""

logging.basicConfig(format='%(name)s %(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)
class Sleeper(VerdictDB):
    def __init__(self, io_loop, sleep, outcome=None):
        self.io_loop = io_loop
        self.log = logging.getLogger(self.__class__.__name__)
        self.sleep = int(sleep)
        self.outcome = float(outcome)

    def generate_query_parameters(self, domain, path_parameters):
        '''
        Method to generates a dict of database query parameters from
        domain and path_parameters. This encapsulates the db schema.
        '''
        pass
    @gen.coroutine
    def lookup(self, domain, path, query_parameters):
        '''
        Lookup domain and path_parameters *asynchronously* and return a Future
        that either yields a verdict if one is available, or None.
        Use generate_query_parameters to map the query arguments to db query
        arguments.
        '''
        yield gen.sleep(self.sleep)
        rand = random.random()
        if rand <= self.outcome:
            result = {'status':True, 'blacklist':rand}
        else:
            result = {'status':False}
        raise gen.Return(result)

    def parse_response(self, res):
        pass
    def insert(self, domain, path, query_parameters, payload):
        pass
    def is_whitelist(self):
        pass
    def priority(self):
        pass
