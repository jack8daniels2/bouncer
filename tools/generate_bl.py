#! /usr/bin/env python

import sys
import random


if len(sys.argv) < 2:
    print '{} num_domains filename'
    sys.exit(-1)

num_domains = int(sys.argv[1])
filename = sys.argv[2]
## seed from filename
charset = filename.rsplit('/', 1)[-1]
length = len(charset)
with open(filename, 'w') as fp:
    for i in xrange(num_domains):
        dn_charset = random.sample(charset, random.randint(length/2, length))
        url = '.'.join(('www', ''.join(dn_charset), 'com'))
        pp_charset = random.sample(charset, 2)
        path = '{0}{1}?{0}=0&{1}=1'.format(pp_charset[0], pp_charset[1])
        fp.write(url + '/' + path + '\n')
