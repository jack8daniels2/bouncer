#### Problem
A micro service that enables its users to lookup urls in blocklists and whitelists. The blocklists and whitelists could be different formats (domain, urls, url + parameters etc) and could be billions of rows large.

#### Design
The HTTP service is implemented using tornado.
Each urlinfo request is first looked up in caches, and if it is a miss, configured databases (potentially of different kinds, storing different block lists) are
queried asynchronously. As soon as the first database responds with a hit, the response is return.
The response is asynchronously written to the respective cache.

Caches and Databases implement a generic storage interface, VerdictCache and VerdictDB respectively. The difference between the two interfaces is that the VerdictDB lookup is a coroutine and returns a Future. Caches are expected to be quicker and its look up is a blocking call. As an example, I implemented 3 different VerdictDB implementations
1. bigtable_example uses cassandra
2. memory_trie maintains a dict[dict[dict[set]]] a trie like structure to store blocklist in memory.
3. sleeper is just for testing. It sleeps for configured time and then reponds with a hit or miss based on configured probability.

And I implemented a VerdictCache over redis configured as an LRU (maxmemory and maxmemory-policy).
Both, the Caches and Databases can be configured using the configuration file.

There are two caches - blacklist and whitelist. Whitelist should be populated with Alexa top 1000 or similar. In absense of it , I store all misses in the whilelist. It is probably better than a static whitelist, since it can handle flash crowds and urls popular in each region.

Response generation is simplistic. One may decide to enhance it in different ways. For example
- We may also wish to aggregate responses, assign weights and/or priority to them.
- We can have an absolute timeout and respond with 'no verdict' if none of the databases respond in that time period. But, it should cache the late responses for subsequent queries for the same url.
- We may also want to keep a hit count for each url, domain etc

Using user specified strings (url) as is in an internal service and database is a bad idea. I'd like to encode the url right away from the service onwards. Encoding TBD.

#####TODO
Automated Testing, packaging, replace sys.argv usage with optparser, verify url parsing logic.

#####Future expansion

> The size of the URL list could grow infinitely, how might you
> scale this beyond the memory capacity of this VM? Bonus if you
> implement this.

The memory_trie storage is an example of how we can maintain the blocklist in memory. I'm not a fan of this idea because scaling and monitoring such an application is not simple.
One option of scaling a service that maintains the blocklist in memory is to shard the key space and assign them to pools of identical server. A reverse proxy would route the request to the right pool. Use of consistent hashing can avoid reassignment of keyspace. I don't recommend an in-memory solution when we are maintaining an 'infinite' list.
Therefore, I implemented a generic storage interface backed by redis, cassandra, in memory dict/trie and riak. The key to the solution is the AnyCast functionality that allows querying multiple 'storage' asynchronously (server can move on to serving other requests) and in parallel, and allow a service to respond as soon as the first hit is received. Redis performs pretty well with large key space and so does Cassandra. We can scale to 'infinite' urls by keeping, say cassandra as a persistent storage, redis as a LRU cache, and still keep our average response to < 5msec.

> The number of requests may exceed the capacity of this VM, how
> might you solve that? Bonus if you implement this.

See above

> What are some strategies you might use to update the service
> with new URLs? Updates may be as much as 5 thousand URLs a day
> with updates arriving every 10 minutes.

We can use a message queue that updates the storage. Each update would first write to the database and then invalidate the corresponding cache entries. Writing to cache first ensures that we use the update right away, but it'd require throwing away some good LRU entries. I implemented tools/data_feed.py and tools/data_ingest.py as a prototype using kafka (it doesn't invalidate the cache though.)
If we were to implement a service that maintains the blacklists in memory then we can upgrade it directly using non-blocking polling (preferrably done by libev).
```python
#In absense of a async hook in python-kafka, one could do periodic non-blocking user level polling
IOLoop.current().call_at(time.time() + self.update_frequency,
                         self.blacklists_update, fetch_num_messages)

def blacklists_update(self, fetch_num_messages):
    for msg in self.consumer.get_messages(count=fetch_num_messages, block=False):
        try:
            msg = json.loads(msg.message.value)
            blacklist_type = msg['type']
            map(partial(self.blacklists.insert, blacklist_type), msg['add'])
            map(partial(self.blacklists.delete, blacklist_type), msg['remove'])
        except:
            self.log.exception('Error ingesting msg {}'.format(msg))
    IOLoop.current().call_at(time.time() + self.update_frequency,
                             self.blacklists_update, fetch_num_messages)
```

> How would you design the system to tolerate component failure
> such that you can achieve 100% uptime.

I believe that the strength of my solution is that storage and updates are separate services allowing us to scale the HTTP service independently. I'd put many instances of this service behind an HAProxy.

####Other ideas
- Rewrite the service in a more network performant language. Go suits the usecase (and is the rage these days)
- Consistent read is not paramount for this use case. I'd lean towards using AP databases like Riak or Cassandra. A benefit of using a BigTable database (like Cassandra) is that we can maintain a single row for each domain with path_and_parameters as dynamic columns to limit the number of rows.
- In order to handle, 'infinite' number of urls, I'd also start thinking about aggregating urls.


######Sample output
```
(bouncer)aahuja-mbp:bouncer aahuja$ python bouncer/app.py config.ini
app 2015-06-12 21:55:44 DB config {'memory_trie': {'filenames': '/tmp/phishing.dat'}, 'sleeper': {'outcome': '0.0', 'sleep': '1'}, 'bigtable_example': {'keyspace': 'malicious', 'host': 'localhost'}, 'keyvalue_example': {'host': 'localhost', 'bucket': "'prod'"}}
app 2015-06-12 21:55:44 Databases: {'memory_trie': <storage.memory_trie.Trie object at 0x10669c550>, 'keyvalue_example': <storage.keyvalue_example.Riak object at 0x1068a2890>, 'bigtable_example': <storage.bigtable_example.Cassandra object at 0x1066cfa90>, 'sleeper': <storage.sleeper.Sleeper object at 0x1066cfa10>}
app 2015-06-12 21:55:44 Cache config {'blacklist': {'class_name': 'storage.lru_cache.LRUCache', 'host': 'localhost', 'db': '1'}, 'whitelist': {'class_name': 'storage.lru_cache.LRUCache', 'host': 'localhost', 'db': '0', 'whitelist': '1'}}
app 2015-06-12 21:55:44 Caches: {'blacklist': <storage.lru_cache.LRUCache object at 0x10667bf90>, 'whitelist': <storage.lru_cache.LRUCache object at 0x10796f410>}
app.handlers.AnyCast 2015-06-12 21:55:58 future returned {'status': False, 'src': 'Trie'}
app.handlers.AnyCast 2015-06-12 21:55:58 future returned {'status': False}
app.handlers.AnyCast 2015-06-12 21:55:58 future returned {'status': True, 'src': 'Cassandra', 'blacklist': u'malicious'}
tornado.access 2015-06-12 21:55:58 200 GET /urlinfo/1/www.d.uamocas.com/li?l=0&i=1 (::1) 6.50ms
app.handlers.AnyCast 2015-06-12 21:55:59 future competed but Anycast is done
app.handlers.URLInfoHandler 2015-06-12 21:56:04 cache hit
tornado.access 2015-06-12 21:56:04 200 GET /urlinfo/1/www.d.uamocas.com/li?l=0&i=1 (::1) 1.33ms
app.handlers.AnyCast 2015-06-12 21:56:39 future returned {'status': True, 'src': 'Trie', 'blacklists': ['phishing']}
app.handlers.AnyCast 2015-06-12 21:56:39 future competed but Anycast is done
tornado.access 2015-06-12 21:56:39 200 GET /urlinfo/1/www.t.pignhsdaih.com/ha?h=0&a=1 (::1) 1.72ms
app.handlers.AnyCast 2015-06-12 21:56:39 future competed but Anycast is done
app.handlers.AnyCast 2015-06-12 21:56:40 future competed but Anycast is done
app.handlers.URLInfoHandler 2015-06-12 21:56:50 cache hit
tornado.access 2015-06-12 21:56:50 200 GET /urlinfo/1/www.t.pignhsdaih.com/ha?a=1&h=0 (::1) 1.24ms
app.handlers.AnyCast 2015-06-12 21:57:14 future returned {'status': False, 'src': 'Trie'}
app.handlers.AnyCast 2015-06-12 21:57:14 future returned {'status': False}
app.handlers.AnyCast 2015-06-12 21:57:14 future returned {'status': False, 'src': 'Cassandra'}
app.handlers.AnyCast 2015-06-12 21:57:15 future returned {'status': False}
tornado.access 2015-06-12 21:57:15 200 GET /urlinfo/1/doesnotexit.com/ha?a=1&h=0 (::1) 1006.82ms
```
