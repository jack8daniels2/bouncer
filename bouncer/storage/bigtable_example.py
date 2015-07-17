import logging
from . import VerdictDB
import utils
from tornado import gen
from tornado.concurrent import Future
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent
from cassandra.encoder import Encoder
from cassandra.query import dict_factory
from cassandra.cluster import Cluster, OperationTimedOut

class TornadoCassandra(object):
    """
    This class attaches Cassandra Futures with Tornado Futures.
    """
    def __init__(self, session, ioloop):
        self._session = session
        self._ioloop = ioloop

    def execute(self, query, parameters=None, trace=False):
        tornado_future = Future()
        cassandra_future = self._session.execute_async(query, parameters, trace)
        self._ioloop.add_callback(
            self._callback, cassandra_future, tornado_future)
        return tornado_future

    def _callback(self, cassandra_future, tornado_future):
        try:
            #This is similar to gen.corouting.Runner()
            result = cassandra_future.result(timeout=0)
        except OperationTimedOut:
            return self._ioloop.add_callback(
                self._callback, cassandra_future, tornado_future)
        except Exception as exc:
            return tornado_future.set_exception(exc)
        tornado_future.set_result(result)

class Cassandra(VerdictDB):
    """
    Setup Database describes the simplistic schema. There is room for improvements there by using
    Set() of query parameters instead of string of query parameters in sorted order.
    """
    def __init__(self, io_loop, host, keyspace='malicious', whitelist=False, setup=False):
        self.whitelist = whitelist
        self.log = logging.getLogger('app.' + self.__class__.__name__)
        self._cluster = Cluster([host,])
        if setup:
            self._session = self._cluster.connect()
            self.setup_database(keyspace)
            self._session.set_keyspace(keyspace)
        else:
            self._session = self._cluster.connect(keyspace)
        if io_loop:
            self._async_session = TornadoCassandra(self._session, io_loop)
        self._session.row_factory = dict_factory

        self._lookup_query = self._session.prepare(
                'SELECT verdict from blacklist WHERE dn = ? and pp = ?;')
        self._insert_query = self._session.prepare(
            'INSERT INTO blacklist (dn, pp, verdict) VALUES (?, ?, ?);')

    def setup_database(self, keyspace):
        statements = [
            """CREATE KEYSPACE %s
            WITH REPLICATION = { 'class': 'SimpleStrategy', 'replication_factor': 1 }
            AND DURABLE_WRITES = true;""" % keyspace,

            "USE %s;" % keyspace,

            """CREATE TABLE IF NOT EXISTS blacklist (
                dn TEXT,
                pp TEXT,
                verdict TEXT,
                PRIMARY KEY(dn, pp)
            );""",

            """CREATE INDEX IF NOT EXISTS
                blacklist_pp ON blacklist (pp);""",
        ]

        for s in statements:
            self._session.execute(s)

    def generate_query_parameters(self, domain, path, query_parameters):
        # parameters should be encoded
        return domain, path + '?' + '&'.join(sorted(query_parameters))

    @gen.coroutine
    def lookup(self, domain, path, query_parameters):
        domain, path_parameters = self.generate_query_parameters(domain, path, query_parameters)
        bound_stmt = self._lookup_query.bind((domain, path_parameters))
        res = yield self._async_session.execute(bound_stmt)
        raise gen.Return(self.parse_response(res))

    def insert(self, payload, url):
        """
        TODO, In order to allow search of query parameters in any order,
        we may be able to use sets. This needs to be investigated.
        For now, we'll sort the query arguments. Yuck!
        """
        dn, path, qp = utils.parse_url(url)
        domain, path_parameters = self.generate_query_parameters(dn, path, qp)
        return self._session.execute(self._insert_query.bind((domain, path_parameters, payload)))

    def delete(self, url):
        raise NotImplementedError

    def parse_response(self, match):
        res = {'src':self.__class__.__name__}
        if match:
            res['status'] = True
            res['blacklist'] = match[0]['verdict']
        else:
            res['status'] = False
        return res

    def is_whitelist(self):
        return self.whitelist

    def priority(self):
        #Not used
        return 0
