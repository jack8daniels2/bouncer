#! /usr/bin/env python

"""
RESTful API to lookup multiple databases for url reputation

"""
import logging
import tornado.web
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging
import sys
import ConfigParser
from handlers import IndexHandler, URLInfoHandler
import storage
import utils

logging.basicConfig(format='%(name)s %(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.ERROR)

class Application(tornado.web.Application):
    def __init__(self, configfile):
        config = ConfigParser.SafeConfigParser()
        config.read(configfile)
        try:
            debug = config.getboolean('general', 'debug')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError) as e:
            debug = False
        enable_pretty_logging()
        self.log = logging.getLogger('app')
        if debug:
            self.log.setLevel(logging.DEBUG)

        handlers = [
            (r"/?$", IndexHandler),
            (r"/urlinfo/1/(?P<dn>[^/]*)/(?P<pp>[^/]*)", URLInfoHandler),
        ]

        tornado.web.Application.__init__(self, handlers, debug=debug)
        # Initalize all backend databases dynamically from the config
        try:
            dbs = map(str.strip, config.get('databases', 'enabled').split(','))
        except:
            self.log.exception('No valid databases provided')
            raise Exception('No valid databases provided')
        dbs_config = {db_name: dict(config.items(db_name)) for db_name in dbs}
        self.log.debug('DB config {}'.format(dbs_config))
        self.dbs = {db_name:self.init_storage(db_name,
                                              db_config,
                                              storage.VerdictDB)
                        for db_name, db_config in dbs_config.iteritems()}
        self.log.info('Databases: {}'.format(self.dbs))
        # Initalize all caches dynamically from the config
        try:
            caches = map(str.strip, config.get('caches', 'enabled').split(','))
        except:
            self.log.exception('No valid caches provided')
            raise Exception('No valid caches provided')
        cache_configs = {cache_name: dict(config.items(cache_name)) for cache_name in caches}
        self.log.debug('Cache config {}'.format(cache_configs))
        self.caches = {cache_name:self.init_storage(cache_name,
                                                    cache_config,
                                                    storage.VerdictCache)
                        for cache_name, cache_config in cache_configs.iteritems()}
        self.log.info('Caches: {}'.format(self.caches))

    def init_storage(self, name, config, baseclass):
        if 'class_name' in config:
            class_name = config.pop('class_name')
            classobject = utils.load_class(class_name, baseclass)
        else:
            classobject = utils.discover_class('.'.join(('storage', name)), baseclass)
        io_loop = IOLoop.current()
        try:
            return classobject(io_loop, **config)
        except:
            self.log.exception('Error initializing storage {} config {}' \
                    .format(classobject, config))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'Usage: {} <config>'.format(sys.argv[0])
        sys.exit(-1)

    app = Application(sys.argv[1])
    app.listen(8080)
    IOLoop.current().start()
