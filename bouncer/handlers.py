import tornado
from tornado.concurrent import Future
from tornado import gen
import logging
from tornado.ioloop import IOLoop
import json
import operator

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        banner = """<pre>
########   #######  ##     ## ##    ##  ######  ######## ########
##     ## ##     ## ##     ## ###   ## ##    ## ##       ##     ##
##     ## ##     ## ##     ## ####  ## ##       ##       ##     ##
########  ##     ## ##     ## ## ## ## ##       ######   ########
##     ## ##     ## ##     ## ##  #### ##       ##       ##   ##
##     ## ##     ## ##     ## ##   ### ##    ## ##       ##    ##
########   #######   #######  ##    ##  ######  ######## ##     ##
        </pre>"""
        self.write(banner)

class AnyCast(Future):
    def __init__(self, futures):
        super(AnyCast, self).__init__()
        #TODO use standard loggers
        self.log = logging.getLogger('app.handlers.' + self.__class__.__name__)
        self.futures = futures
        for future in self.futures:
            future.add_done_callback(self.done_callback)

    def done_callback(self, future):
        if self.done():
            self.log.debug('future completed but Anycast is done')
            return
        result = future.result()
        self.log.debug('future returned {}'.format(result))
        if result['status'] == True or all([f.done() for f in self.futures]):
            self.set_result(result)

class URLInfoHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = ("GET",)

    @gen.coroutine
    def get(self, dn, pp):
        self.log = logging.getLogger('app.handlers.' + self.__class__.__name__)
        qp = [k + '=' + v[-1] for k,v in self.request.arguments.items()]
        #cache lookup can be asynchronous. for redis it http basically.
        cache_res = filter(operator.truth,
                       [cache.lookup(dn, pp, qp) for cache in self.application.caches.values()])
        if cache_res:
            self.log.debug('cache hit')
            res = cache_res[0]
            self.write(res)
            return
        futures = [db.lookup(dn, pp, qp) for db in self.application.dbs.values()]
        db_res = yield AnyCast(futures)
        if db_res['status']:
            blacklist_caches = filter(lambda c: not c.is_whitelist,
                                    self.application.caches.values())
            for cache in blacklist_caches:
                IOLoop.current().spawn_callback(
                    self.application.caches['blacklist'].insert, dn, pp, qp, db_res)
        else:
            # Due to lack of a pre-populated whitelist, we can maintain one based
            # popular non-malicious urls.
            whitelist_caches = filter(lambda c: c.is_whitelist,
                                    self.application.caches.values())
            for cache in whitelist_caches:
                IOLoop.current().spawn_callback(cache.insert, dn, pp, qp, db_res)

        self.write(db_res)
