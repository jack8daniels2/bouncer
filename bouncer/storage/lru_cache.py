import redis
from . import VerdictCache

"""
Redis with maxmemory and maxmemory-policy allkeys-lru
allows redis to behave like an LRU cache withoyt using TTL.
We can also implement TTLs if need be.

Used for both the blacklist and whitelist. Whitelist should be pre-populated
from Alexa top 10000 equivalent.
Blacklists, specially containing DGAs, would follow a zipf distribution and would
benefit from a cache.
"""

class LRUCache(VerdictCache):
    def __init__(self, io_loop, host, db, whitelist=False):
        self.redis = redis.Redis(host, db=db)
        self.whitelist = bool(whitelist)

    def generate_query_parameters(self, domain, path, query_parameters):
        '''
        Method to generates a dict of database query parameters from
        domain and path_parameters. This encapsulates the db schema.
        '''
        return domain + '/' + path + '?' + '&'.join(sorted(query_parameters))

    def lookup(self, domain, path, query_parameters):
        '''
        Lookup domain and path_parameters *asynchronously* and return a Future
        that either yields a verdict if one is available, or None.
        Use generate_query_parameters to map the query arguments to db query
        arguments.
        '''
        key = self.generate_query_parameters(domain, path, query_parameters)
        return self.redis.hgetall(key)

    def insert(self, domain, path, query_parameters, payload):
        '''
        Insert key into the cache
        '''
        key = self.generate_query_parameters(domain, path, query_parameters)
        self.redis.hmset(key, payload)

    @property
    def is_whitelist(self):
        '''
        In case, we want to maintain separate DBs for whitelist too, this
        proprerty will help differentiate them from blacklists.
        '''
        return self.whitelist
    def parse_response(self, res):
        pass
    def priority(self):
        pass
