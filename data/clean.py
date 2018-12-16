#!/usr/bin/env python3

import os
import pickle

import sys
sys.path.insert(0, '/home/tama/bot/dataAPI')
import serverAPI
import channelAPI

def archive_channel(folder, cid, test):
    full_path = '{0}/{1}'.format(folder, cid)
    print("delete {0}".format(full_path))
    if test != "1":
        os.remove(full_path)
            
if __name__ == '__main__':
    test = sys.argv[1] if len(sys.argv) > 1 else "0"
    whitelist = [line.strip() for line in open("whitelist", "r")]
    for folder in os.listdir('.'):
        if folder.isnumeric():
            s = serverAPI.ServerAPI('/home/tama/bot', folder)
            clist = s.get_channel_list()
            if clist is None:
                continue
            for cid in clist:
                try:                    
                    channel = channelAPI.ChannelAPI('/home/tama/bot', folder, cid, {})
                    print('[{0}] {1}'.format(folder, channel.get_name()))
                    if str(cid) in whitelist:
                        continue

                    if channel.is_ex_raid() is False:
                        archive_channel(folder, cid, test)
                except:
                    continue

        channels_filepath = '{0}/channels'.format(folder)
        if not os.path.exists(channels_filepath):
            continue

        d = pickle.load(open(channels_filepath, 'rb'))
        for k in list(d):
            filepath = '{0}/{1}'.format(folder, k)
            if not os.path.exists(filepath):
                del d[k]

        pickle.dump(d, open(channels_filepath, 'wb'))


