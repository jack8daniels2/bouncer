from abc import ABCMeta, abstractmethod, abstractproperty
from tornado import gen

class VerdictBase(object):
    __metaclass__ = ABCMeta
    @abstractmethod
    def generate_query_parameters(self, domain, path_parameters):
        '''
        Method to generates a dict of database query parameters from
        domain and path_parameters. This encapsulates the db schema.
        '''
        pass
    @abstractmethod
    def insert(self, domain, path, query_parameters, payload):
        '''
        Insert key into the cache
        '''
        pass
    @abstractmethod
    def parse_response(self, res):
        '''
        Map response to generic format that the caller expects. Another encapsulation
        over the schema.
        '''
        pass
    @abstractproperty
    def is_whitelist(self):
        '''
        In case, we want to maintain separate DBs for whitelist too, this
        proprerty will help differentiate them from blacklists.
        '''
        pass
    @abstractproperty
    def priority(self):
        '''
        In case, we need to aggregate multiple dbs, priority will help
        break a tie
        '''
        pass

class VerdictDB(VerdictBase):
    """
    VerdictDB.lookup is a coroutine and returns a Future to support asynchronous lookups
    """
    __metaclass__ = ABCMeta
    @abstractmethod
    @gen.coroutine
    def lookup(self, domain, path, query_parameters):
        '''
        Lookup domain and path_parameters *asynchronously* and return a Future
        that either yields a verdict if one is available, or None.
        Use generate_query_parameters to map the query arguments to db query
        arguments.
        '''
        pass

class VerdictCache(VerdictBase):
    """
    VerdictCache.lookup should be really fast since it a blocking call.
    """
    __metaclass__ = ABCMeta
    @abstractmethod
    def lookup(self, domain, path, query_parameters):
        '''
        Lookup domain and path_parameters *asynchronously* and return a Future
        that either yields a verdict if one is available, or None.
        Use generate_query_parameters to map the query arguments to db query
        arguments.
        '''
        pass
