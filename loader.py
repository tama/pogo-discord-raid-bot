#!/usr/bin/env python3.5

import os
import sys
from plugins.plugin import Plugin
from pydoc import locate

def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses

def get_plugins(path, silent = False):
    plugins = {}
    sys.path.insert(0, path);
    for f in os.listdir(path):
        fname, ext = os.path.splitext(f)
        if ext == '.py':
            if silent is False:
                print("{0}{1}".format(fname, ext))
            mod = locate(fname, forceload=1)
    sys.path.pop(0)

    for p in get_all_subclasses(Plugin):
        if silent is False:
            print(p)
        
        if p.name in plugins:
            continue

        tmp = p()
        plugins[p.name] = p
    return plugins

if __name__ == '__main__':
    print(get_plugins("./plugins"))

