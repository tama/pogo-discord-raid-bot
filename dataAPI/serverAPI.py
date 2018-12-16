#!/usr/bin/env python3.5

import sys
sys.path.insert(0, '/home/tama/bot')

import os
import pickle
import loader

class ServerAPI:
    def __init__(self, basepath, servid):
        self.basepath = basepath
        self.servid = servid
        self.dataFolder = "{0}/data/{1}".format(basepath, servid)
        
    def get_channel_list(self):
        cFilePath = "{0}/channels".format(self.dataFolder)
        if not os.path.exists(cFilePath):
            return None
        
        self.data = pickle.load(open(cFilePath, "rb"))
        return [k for k in self.data]

    def get_gym_list(self):
        gFilePath = "{0}/gym_with_coords".format(self.dataFolder)
        if not os.path.exists(gFilePath):
            return None

        res = []
        lines = [line.strip() for line in open(gFilePath, "r", encoding="utf8")]
        for l in lines:
            parts = l.split(";")
            try:
                if len(parts) < 6:
                    res.append((parts[0], parts[1], parts[2], parts[3].encode(), parts[4].encode(), False))
                else:
                    isEx = (parts[4] == "EX")
                    res.append((parts[0], parts[1], parts[2], parts[3].encode(), parts[4].encode(), isEx))
            except Exception as e:
#                print(e)
                pass
        return res

    def get_handler(self):
        plugins = loader.get_plugins("/home/tama/bot/plugins", True)
        conffile = '{0}/data/{1}/conf'.format(self.basepath, self.servid)
        if os.path.exists(conffile):
            conf_lines = [line.strip() for line in open(conffile, 'r')]
            handler_name = "default"
            for line in conf_lines:
                if line.startswith('#'):
                    continue

                key = line.split(':')[0].strip()
                if key == 'handler':
                    handler_name = line.split(':')[1].strip()
                    break
        return plugins[handler_name]()
        
if __name__ == "__main__":
    s = ServerAPI(322379168048349185)
#    print(s.get_channel_list())
#    print(s.get_gym_list())
    print(s.get_handler().get_instinct_role())
