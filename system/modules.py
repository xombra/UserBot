# -*- coding: utf-8 -*-
from os.path import split
import logs
import glob
import imp
import sys

cmp = {}   # lint:ok


def find(module=''):
    for i in glob.glob("modules/*.py" if not module else module):
        i = i.replace('.py', '')
        cmp[split(i)[1]] = imp.find_module(i)
        logs.info('%s: Search %s' % (__name__, i))


def load(module):
    a, b, c = cmp[module]
    cmp[module] = imp.load_module(module, a, b, c)
    logs.info('%s: Load %s' % (__name__, module))


def download(module, delete=False):
    cmp[module].core.removeHandler(module)
    if delete:
        del sys.modules[module]
        del cmp[module]


def reload(module):
    download(module, True)
    find('modules/%s.py' % module)
    load(module)