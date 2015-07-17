#! /usr/bin/env python
from kafka import KafkaClient, SimpleProducer, SimpleConsumer
import ConfigParser
import sys
import itertools
import json

config = ConfigParser.SafeConfigParser()
config.read(sys.argv[1])
kafka_client = KafkaClient(config.get('data_feed','host'))
producer = SimpleProducer(kafka_client,
                          async=True)
consumer = SimpleConsumer(kafka_client,
                          group=config.get('data_feed', 'group'),
                          topic=config.get('data_feed', 'topic'))
fetch_num_messages = config.getint('data_feed', 'fetch_num_messages')
while True:
    for msg in consumer.get_messages(count=fetch_num_messages, block=True):
        producer.send_messages(config.get('data_feed','topic'), msg.message.value)
