#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Usage:
    gtd start <name>
    gtd stop
    gtd status
'''
import pickle
import datetime
import docopt
import sys

args = docopt.docopt(__doc__)

now = datetime.datetime.now()

if args['start']:
    data = {'time': now, 'name': args['<name>']}
    with open('data', 'w') as f:
        pickle.dump(data, f)

if args['stop']:
    pass
if args['status']:
    with open('data', 'r') as f:
        d = pickle.load(f)
    print('%s: %s' % (d['name'], now - d['time']))
