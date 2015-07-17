from collections import defaultdict
import logging
from tornado import gen
from . import VerdictDB
from tornado.concurrent import Future
import utils

"""
This class loads blacklists from a bunch of files and stores them in a trie like format.
- store blacklists in a trie like format to save space (multiple urls with same domain or domain and path)
    {bl_type:{domain:{path:Set(query_parameter)}}}
- It also allows matching urls with query parameters in a different order
- It can also allows matching urls with a subset of query parameters
"""

class Trie(VerdictDB):
    def __init__(self, whitelist=False, filenames = None):
        # {bl_type: {domains:{paths:set(query_parameters)}}
        self.blacklists = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        self.whitelist = whitelist
        self.log = logging.getLogger('app.' + self.__class__.__name__)
        if filenames:
            filenames = map(str.strip, filenames.split(','))
            for filename in filenames:
                list_type = filename.rsplit('/', 1)[-1].split('.', 1)[0]
                self.load_file(list_type, filename)

    def generate_query_parameters(self, domain, path, query_parameters):
        qp = frozenset(query_parameters)
        return domain, path, qp

    def lookup_url(self, url):
        dn, path, qp = utils.parse_url(url)
        dn, path, qp = self.generate_query_parameters(dn, path, qp)
        match = [bl_type for bl_type, bl in self.blacklists.iteritems()
                    if qp in bl[dn][path]]
        res = {}
        if match:
            res['status'] = True
            res['blacklists'] = match
        else:
            res['status'] = False
        return res

    @gen.coroutine
    def lookup(self, domain, path, query_parameters):
        domain, path, qp = self.generate_query_parameters(domain, path, query_parameters)
        match = [bl_type for bl_type, bl in self.blacklists.iteritems()
                    if qp in bl[domain][path]]
        raise gen.Return(self.parse_response(match))

    def parse_response(self, match):
        res = {'src':self.__class__.__name__}
        if match:
            res['status'] = True
            res['blacklists'] = match
        else:
            res['status'] = False
        return res

    def insert(self, bl_type, url):
        dn, path, qp = utils.parse_url(url)
        dn, path, qp = self.generate_query_parameters(dn, path, qp)
        try:
            self.blacklists[bl_type][dn][path].add(qp)
        except KeyError:
            return

    def load_file(self, bl_type, filename):
        with open(filename, 'r') as fp:
            for line in fp:
                try:
                    self.insert(bl_type, line.strip())
                except:
                    self.log.exception('Unable to parse %s from %s', line, filename)

    @property
    def is_whitelist(self):
        return self.whitelist

    def priority(self):
        return 0

    # def __repr__(self):
    #     return self.blacklists.__repr__()
