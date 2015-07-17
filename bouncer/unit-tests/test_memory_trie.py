import logging
from storage import memory_trie
import unittest

class TestBlacklist(unittest.TestCase):
    def test_lookup(self):
        url1 = 'www.a.b.com/1/2/3?x=a&y=b'
        url2 = 'www.a.b.com/1/2/3?y=b&x=a'
        bl = memory_trie.Trie()
        bl.insert_record('test', url1)
        res = bl.lookup_url(url1)
        self.assertTrue(res['status'])
        self.assertEqual(tuple(res['blacklists']), ('test',))
        res = bl.lookup_url(url2)
        self.assertTrue(res['status'])
        self.assertEqual(tuple(res['blacklists']), ('test',))

    def test_multiple(self):
        url1 = 'www.a.b.com/1/2/3?x=a&y=b'
        url2 = 'www.a.b.com/1/2/3?y=b&x=a'
        url3 = 'www.a.b.com/1/2/3?y=b'
        bl = memory_trie.Trie()
        for bl_type in ['test1','test2']:
            for url in [url1, url2]:
                bl.insert_record(bl_type, url)
        bl.insert_record('test2', url3)
        bl.insert_record('test3', url3)
        res = bl.lookup_url(url1)
        self.assertTrue(res['status'])
        self.assertEqual(set(res['blacklists']), set(('test1','test2')))
        res = bl.lookup_url(url3)
        self.assertTrue(res['status'])
        self.assertEqual(set(res['blacklists']), set(('test2', 'test3')))

    def test_lookup_url_negative(self):
        url1 = 'www.a.b.com/1/2/3?x=a&y=b'
        url2 = 'www.a.b.com/1/2/3?x=a'
        bl = memory_trie.Trie()
        bl.insert_record('test', url1)
        res = bl.lookup_url(url2)
        self.assertFalse(res['status'])

if __name__ == '__main__':
    logging.basicConfig(format='%(name)s %(asctime)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.DEBUG)
    unittest.main()
