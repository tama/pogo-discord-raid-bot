#!/usr/bin/env python3.5
# coding: utf-8

import pickle
import os
import re

from collections import OrderedDict

class ChannelAPI:
    delta = 5

    def __init__(self, basepath, servid, cid, ref):
        self.path = "{0}/data/{1}/{2}".format(basepath, servid, cid)
        self.needSync = True
        self.ref = ref
        self.reload()

    #
    # Reload data from file
    #   
    def reload(self):
        try:
            self.data = pickle.load(open(self.path, "rb"))
            self.name = self.data["name"]
            self.needSync = False
        except Exception as e:
            raise Exception("Error while reading file, the format of the file may be incorrect (error message: " + str(e) + ")")

    # --------------
    # Read methods
    # --------------

    #
    # General
    #
    def get_name(self):
        return self.name

    def get_poke(self):
        poke = "-".join([x for x in self.name.split("-")[:-2]])
        if '-' in poke:
            poke = '-'.join([x for x in poke.split('-')[1:]])
        return poke

    def get_loc(self):
        return self.name.split("-")[-2]

    def get_time(self):
        end_time_hm = [int(x) for x in self.name.split("-")[-1].replace('fin', '').split('h')]
        start_time_hm = [end_time_hm[0], end_time_hm[1] - 45]
        if start_time_hm[1] < 0:
            start_time_hm = [start_time_hm[0] - 1, start_time_hm[1] + 60]
        return [start_time_hm[0], start_time_hm[1], end_time_hm[0], end_time_hm[1]]
    
    def is_ex_raid(self):
        return 'deox' in self.get_poke()

    #
    # Session/Player data
    #
    def is_session_opened(self):
        session_list = self.get_session_list()
        return len(session_list) > 1 or session_list[0] != '00:00'

    def find_session(self, session):
        self.check_valid_session(session)
        this_m = 60 * int(session.split(':')[0]) + int(session.split(':')[1])
        session_list = self.get_session_list()
        found_session = None
        for s in session_list:                   
            sess_m = 60 * int(s.split(':')[0]) + int(s.split(':')[1])
            if abs(this_m - sess_m) <= ChannelAPI.delta:
                found_session = s
                break
        return found_session
           
    def get_session_list(self):
        if self.needSync is True:
            raise Exception("Data is not up to date, call reload")
        
        return sorted(list(self.data['player_list'].keys()))

    def get_player_list(self, session = None):
        self.check_valid_session(session)
        if session is not None and session not in self.data['player_list']:
            raise Exception("Unknown session") 

        res = set()
        if session is None:
            sessions_list = self.get_session_list()
            for s in sessions_list:
                for pkey in self.data['player_list'][s]:
                    res.add((s, pkey))
        else:
           for pkey in self.data['player_list'][session]:
                res.add((session, pkey)) 
        return sorted(list(res))

    def get_total_count(self, session = None):
        total = 0
        if session is None:
            sessions = self.get_session_list()
            players = {}
            for s in sessions:
                players_in_session = self.get_player_list(s)
                for p in players_in_session:
                    if p[1] not in players:
                        pdata = self.get_player_data(p[1], s)
                        players[p[1]] = 1 + pdata.extra
            for p in players:
                total += players[p]
        else:
            player_list = self.get_player_list(session)
            total = 0
            for p in player_list:
                total += self.data['player_list'][p[0]][p[1]].extra + 1
        return total

    def get_count_role(self, role1, role2, session):
        self.check_valid_session(session)
        plist = self.get_player_with_role(role1, role2, session)
        total = 0
        for x in plist:
            total += x[1]
        return total

    def get_player_with_role(self, role1, role2, session):
        self.check_valid_session(session)
        if role1 != 'unknown':
            try:
                roleIndex = ['yellow', 'blue', 'red'].index(role2)
            except ValueError:
                raise Exception("Invalid role2 (possible values : yellow, red, blue")
                pass

        plist = self.get_player_list(session)
        tmp = OrderedDict()
        for p in plist:
            cnt = 0
            pdata = self.data['player_list'][p[0]][p[1]]

            if len(pdata.roles) == 0:
                if role1 == 'unknown':
                    cnt = 1 + pdata.extra
            else:
                if role1 != 'unknown' and sum(pdata.teams) == 1 + pdata.extra:
                    cnt = pdata.teams[roleIndex]
                elif role1.lower() == pdata.roles[0].lower():
                    cnt = 1 + pdata.extra
                
            if cnt > 0:
                if p[1] not in tmp:
                    tmp[p[1]] = 0
                tmp[p[1]] += cnt

        # Final result
        res = []
        for k in tmp:
            res.append((k, tmp[k]))
        return res

    def search(self, pname, session = None):
        self.check_valid_session(session)
        plist = self.get_player_list(session)
        res = []
        for p in plist:
            if p[1] == pname:
                res.append((p[0], self.data['player_list'][p[0]][p[1]]))
        return res

    def get_player_data(self, pname, session = '00:00'):
        if pname not in self.data['player_list'][session]:
            raise Exception("Data player not found")
        return self.data['player_list'][session][pname]
    
    #--------------
    # Write methods
    # --------------

    def update(self, pname, pdata, session = None):
        self.check_valid_session(session)
        ret_code = 0
        self.reload()
        old = self.search(pname)

        if len(old) > 1:
            # Multiple entries for this name, return an error code
            return -1

        time = None
        if len(old) <= 1:
            if session is not None:
                new_session = False

                if self.is_session_opened() is False:
                    new_session = True
                else:
                    found_session = self.find_session(session)
                    if found_session is None:
                        new_session = True
                    else:
                        time = found_session
                        
                if new_session is True:
                    session_already_opened = self.is_session_opened()
                    self.open_session(session)

                    if session_already_opened is False:
                        plist = self.get_player_list()
                        for p in plist:
                            self.move(p[1], p[0], session)
                    time = session
                    ret_code = 1

        if session is None:
            time = '00:00'
                    
        self.data['player_list'][time][pname] = pdata
        self.commit()
        return ret_code

    def open_session(self, session):
        self.check_valid_session(session)
        self.reload()
        if session in self.data['player_list']:
            raise Exception("Session already open")
        self.data['player_list'][session] = OrderedDict()

    def move(self, pname, old, new):
        sessions_list = self.get_session_list()
        if self.is_session_opened() is True and new not in sessions_list:
            raise Exception("Unknown destination session")
        
        p = self.search(pname, new)
        if len(p) > 0:
            raise Exception("Can't move, already in destination")

        if old not in sessions_list:
            raise Exception("Unknown source session")
        if pname not in self.data['player_list'][old]:
            raise Exception("Player data not found in source session")
        
        self.data['player_list'][new][pname] = self.data['player_list'][old][pname]
        return self.remove(pname, old)

    def remove(self, pname, session = '00:00'):
        ret_code = 0
        self.check_valid_session(session)
        found = self.search(pname, session)
        if len(found) == 0:
            raise Exception("Player not found in session")
        del(self.data['player_list'][session][pname])
        if len(self.data['player_list'][session]) == 0:
            del(self.data['player_list'][session])
            ret_code = 1

        self.commit()
        return ret_code

    def commit(self):
        pickle.dump(self.data, open(self.path, "wb"))
        self.reload()
    
    # --------------
    # String representation of file
    # --------------
    def read(self):
        session_list = self.get_session_list()
        res = OrderedDict()
        for session in session_list:
            subsession = OrderedDict()
            for r in self.ref:
                if r[1] not in subsession:
                    subsession[r[1]] = []
                ps = self.get_player_with_role(r[0], r[1], session)
                for p in ps:
                    subsession[r[1]].append((p[0].decode('utf-8'), p[1], self.get_player_data(p[0], session)))
                    
                if len(subsession[r[1]]) == 0:
                    del(subsession[r[1]])
            if len(subsession) > 0:
                res[session] = subsession
        return res
    
    def __str__(self):
        res = ""
        orderedData = self.read()
        for s in orderedData:
            res += "[{0}]".format(s)
            res += os.linesep
            for r in orderedData[s]:
                for p in orderedData[s][r]:
                    res += "{0} {1} x {2} \"{3}\"".format(r, p[0], p[1], p[2].extra_msg)
                    res += os.linesep
        return res

    # --------------
    # Utils
    # --------------    
    def check_valid_session(self, session):
        if session is None:
            return
        
        m = re.match('[0-9]{2}:[0-9]{2}', session)
        if m is None:
            raise Exception("Invalid session format : please enter session time as HH:MM")
        
def testAPI():
    ref = [('yellow team', 'yellow'), ('red team', 'red'), ('blue team', 'blue')]
    x = ChannelAPI("322379168048349185", "453264645919080448", ref)
    print(str(x).encode('utf-8'))
    # Get all blue players


if __name__ == '__main__':
    testAPI()
