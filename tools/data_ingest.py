#! /usr/bin/env python
from kafka import KafkaClient, SimpleConsumer
import ConfigParser
import sys
from functools import partial
import json
import utils
import storage

if len(sys.argv) < 2:
    print 'Usage: {} <config>'.format(sys.argv[0])
    sys.exit(-1)

config = ConfigParser.SafeConfigParser()
config.read(sys.argv[1])

#initalize data_feed
data_feed = KafkaClient(config.get('data_feed', 'host'))
consumer = SimpleConsumer(data_feed,
                          group=config.get('data_feed', 'group'),
                          topic=config.get('data_feed', 'topic'))
fetch_num_messages = config.getint('data_feed', 'fetch_num_messages')
#initialize data_sink
sink_config = dict(config.items('data_sink'))
class_name = sink_config.pop('class')
classobject = utils.load_class(class_name, storage.VerdictDB)
db = classobject(None, **sink_config)
removed = added = 0
for msg in consumer.get_messages(count=fetch_num_messages, block=False):
    try:
        msg = json.loads(msg.message.value)
        blacklist_type = msg['type']
        map(partial(db.insert, blacklist_type), msg['add'])
        added += len(msg['add'])
        map(partial(db.delete, blacklist_type), msg['remove'])
        removed += len(msg['remove'])
    except Exception as e:
        print '[{}] Error ingesting msg {}'.format(e, msg)
print 'added %d urls removed %d urls' % (added, removed)
