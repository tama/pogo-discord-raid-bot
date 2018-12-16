#!/usr/bin/env python3.5
#coding: utf8

from plugins.plugin import Plugin
import datetime
import re
import pickle

class Default(Plugin):
        name = 'default'
        channel_pattern = '(.*-fin-*[0-9]([0-9])*h([0-9][0-9])*)|([0-9]([0-9])*h([0-9][0-9])*-.*)'
        trigger_pattern = "^(je suis |on est ){0,1}(((((([\+-]{0,1} {0,1}[0-9]+) {0,1}){0,1}(ok |dispo |chaud ))|([\+-]{0,1} {0,1}[0-9]+) )((pour |à |a ){0,1}([0-9]{1,2}:[0-9]{2}|[0-9]{1,2}( {0,1}h {0,1}| {0,1}H {0,1})([^0-9 ]|$)|[0-9]{1,2}( {0,1}h {0,1}| {0,1}H {0,1})[0-9]{2}))( {0,1})|((([\+-]{0,1} {0,1}[0-9]+) ){0,1}(dispo|chaud) {0,1})|(([\+-] {0,1}[0-9]+) {0,1}))\({0,1}(([0-9]+(, {0,1}[0-9]+)*)+\)){0,1})(.*)$"
        
        def __init__(self):
                pass

        def get_welcome_message(self):
            return '''
    [This message will automatically update with participating players list]
    Example of messages recognized by the bot :
      * dispo
      * Je suis dispo pour 12h30 je suis pas loin
      * On est 3 pour 12h
      * +2 à 13h15
      * +1 13h15
      * -1 13h15
    A recognized message will have a checkmark when correctly processed by the bot.
    In case of bug, ping @tama#9741
    '''
        
        def is_raid_channel(self, name):
            p = re.compile(Default.channel_pattern)
            m = p.match(name)
            if m is None:
                return None

            what = '-'.join(name.split('-')[:-3])
            loc = name.split('-')[-2]
            data = name.split('-')[-1]
            return (what, loc, data)

        def is_message_valid(self, message):
            pattern = re.compile(Default.trigger_pattern, re.IGNORECASE)
            m = pattern.match(message)

            if m is not None:
                return True
            return False

        def parse_message(self, message, message_content):
            pattern = re.compile(Default.trigger_pattern, re.IGNORECASE)
            m = pattern.match(message_content)

            channel_data = load("data/{0}/{1}".format(message.channel.guild.id, message.channel.id))
            player_list = channel_data["player_list"]
            sessions_list = channel_data["sessions_list"]

            auto_moved = False
            
            if m.groups()[16] is not None or m.groups()[20] is not None:
                # "Dispo" without time
                if m.groups()[16] is not None:
                    if m.groups()[18] is not None:
                        # +N dispo
                        nb = int(m.groups()[17].replace(' ', ''))
                    else:
                        # dispo
                        nb = 1
                else:
                    # +N without time
                    nb = int(m.groups()[20])

                # check if there's already a session opened
                if len(sessions_list) > 0:
                    first_non_zero_session_found = None
                    for session in sessions_list:
                        if session.time() > datetime.time(0, 0):
                            first_non_zero_session_found = session
                            break

                    if first_non_zero_session_found is not None:
                        hour = session.strftime("%H:%M")
                        auto_moved = True
                    else:
                        hour = '00h00'
                else:
                    # no session opened yet, hour will be updated when someone submits one
                    hour = '00h00'

            elif m.groups()[8] is not None:
                # +3 pour ...
                nb = int(m.groups()[8].replace(' ', ''))
                hour = m.groups()[11].replace(' ', '')
            elif m.groups()[5] is not None:
                # +2 dispo pour ...
                nb = int(m.groups()[5].replace(' ', ''))
                hour = m.groups()[11].replace(' ','')
            else:
                # dispo pour ...
                nb = 1
                hour = m.groups()[11].replace(' ', '')

            # lv list
            lvs = []
            if m.groups()[23] is not None:
                lvs = [int(lv.strip()) for lv in m.groups()[23].split(',')]

            if m.groups()[25] is not None:
                extra_msg = m.groups()[25]
            else:
                extra_msg = None

            out = (nb, hour, lvs, extra_msg, auto_moved)
            return out

        def get_instinct_emoji(self):
            return 'Instinct'

        def get_mystic_emoji(self):
            return 'Mystic'

        def get_valor_emoji(self):
            return 'Valor'
    
        def get_instinct_role(self):
            return 'Yellow Team'

        def get_mystic_role(self):
            return 'Blue Team'

        def get_valor_role(self):
            return 'Red Team'

        def get_archive_channel_name(self, name):
            return 'archive'
    
def load(filename):
        return pickle.load(open(filename, "rb"))
