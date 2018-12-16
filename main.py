#!/usr/bin/env python3.5
# coding: utf8

import discord
import os
import re
import Player

import pickle
import traceback

import geopy.distance

import loader
import time

from dataAPI import channelAPI
from collections import OrderedDict
from operator import itemgetter

client = discord.Client()

conf = {}
handlers = {}

# Minimal time for 2 sessions to be considered different (in seconds)
max_time_between_sessions = 299
nb_to_emoji = [':zero:', ':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:', ':keycap_ten:']

def get_token():
    token = None
    with open(".token", "r") as f:
        token = f.read()
    return token

@client.event
async def on_guild_channel_create(channel):
    h = handlers[channel.guild.id]

    if h.is_disabled() is True:
        print("Bot is disabled on this server")
        return

    irc = h.is_raid_channel(channel.name)

    if irc is None:
        return

    what = irc[0]
    loc = irc[1]
    data = irc[2]

    await summon_bot(channel)
    await move_to_category(channel, loc)
    
    filename = "data/{0}/gym_with_coords".format(channel.guild.id)
    gym_data = {}
    this_loc = None
    if os.path.exists(filename):
        gyms = [line.strip() for line in open(filename, "r", encoding="utf8")]
        for gym in gyms:
            l = gym.split(";")[0]
            gym_data[l] = (gym.split(';')[1], gym.split(';')[2])

    this_end_time = re.sub('[^0-9]', '', channel.name.split('-')[-1])
    ctime = time.strftime('%H%M', time.localtime())
    if this_end_time > ctime and this_loc is not None:
        try:
            for oc in channel.guild.channels:
                other_loc = None
                bot_in_other_channel = os.path.exists("data/{0}/{1}".format(channel.guild.id, oc.id))
                if bot_in_other_channel is False:
                    continue
                end_time = re.sub('[^0-9]', '', oc.name.split('-')[-1])

                if end_time < ctime:
                    continue
                other_loc_name = oc.name.split('-')[1]
                if other_loc_name in gym_data:
                    other_loc = (gym_data[other_loc_name][0], gym_data[other_loc_name][1])
                    d = geopy.distance.vincenty(this_loc, other_loc).meters
                    if d > 0 and d < 500:
                        await channel.send(content = 'Un autre raid est disponible à proximité : <#{0}>'.format(oc.id))
                        await oc.send(content = 'Un autre raid est disponible à proximité : <#{0}>'.format(channel.id))
        except Exception as e:
            print(e)


async def move_to_category(channel, loc):
    filename = "data/{0}/category".format(channel.guild.id)
    if not os.path.exists(filename):
        return

    print("1")
    mapping = {}
    lines = [line.strip() for line in open(filename, "r", encoding="utf8")]
    for line in lines:
        gym_data = line.split(':')[0]
        gym_cat = line.split(':')[1]
        mapping[gym_data] = gym_cat

    print("2")
    foundcat = None
    if loc in mapping:
        # Try to find the category corresponding to this gym
        for cat in channel.guild.categories:
            print(cat.name)
            if cat.name.lower() == mapping[loc].lower():
                foundcat = cat
                break

    print(foundcat)
    if foundcat is not None:
        await channel.edit(category=foundcat)
        
@client.event
async def on_guild_channel_update(old, new):
    new_name = get_channel_name_with_participants(new)
    if new_name != new.name:
        await new.edit(name=new_name)

async def summon_bot(channel):
    h = handlers[channel.guild.id]
    if h.is_disabled() is True:
        print("Bot is disabled on this server")
        return
    
    print("Bot summoned, please wait.")

    # Load data
    filename = "data/{0}/channels".format(channel.guild.id)
    if not os.path.exists(filename):
        channels = {}
    else:
        channels = load(filename)

    channel_id = channel.id

    # Already summoned...
    if channel_id in channels:
        print("Hey I'm already here !")
        return

    h = handlers[channel.guild.id]
    first_content = h.get_welcome_message()
    msg = await channel.send(content=first_content)
    await msg.pin()
    channels[channel_id] = msg.id
    save(filename, channels)
    channel_data = { "player_list": {}, "sessions_list": [], "name": channel.name }
    save("data/{0}/{1}".format(channel.guild.id, channel_id), channel_data)
    return msg

@client.event
async def on_ready():
    # Check if there are new servers on which the bot was installed before doing anything
    for server in client.guilds:
        print("{0} {1} -> {2}".format(server.id, server.name.encode('utf8'), conf[server.id]["handler"]))
        folder_lookup_name = "/home/tama/bot/data/{0}".format(server.id)
        if not os.path.exists(folder_lookup_name):
            print("[NEW SERVER] {0} ({1})".format(server.id, server.name.encode('utf8')))
            handlers[server.id] = plugins["default"]()
            os.makedirs(folder_lookup_name)
            
    print("Connected !")

    try:
        with open("/home/tama/error/start.txt",  "w", encoding="utf8") as start_txt:
            msg = '''
                `raid-rsvp-bot` started
            '''
            start_txt.write(msg)
    except Exception:
        pass

@client.event
async def on_message(message):
    await process(message)

async def process(message, content = None, user = None, is_sync = False):
    h = handlers[message.channel.guild.id]
    if h.is_disabled() is True:
        return

    # Check if the bot is watching this channel
    h = handlers[message.channel.guild.id]
    filename = "data/{0}/channels".format(message.channel.guild.id)
    if not os.path.exists(filename):
        channels = {}
    else:
        channels = load(filename)

    message_content = content if content is not None else message.content
    sender = user if user is not None else message.author

    words = message_content.split()

    print(message_content.encode())
    if ';' in message_content:
        for subcmd in message_content.split(';'):
#            print("Process : {0}".format(subcmd.strip()))
            await process(message, subcmd.strip(), user)
        return

    roles = discord.utils.get(message.guild.members, name=message.author.name).roles
    is_modo = False
    modo_roles = h.get_modo_roles()
    for r in roles:
        if r.name in modo_roles:
            is_modo = True
            break

    ptrn = re.compile('\[(.*)\] (.*)')
    if is_modo is True and user is None:
        m = re.match(ptrn, message.content)
        if m is not None:
#            print(m.groups())
            await impersonate(m.groups()[0], m.groups()[1], message)
        
    if content is None and len(words) > 1:
        # @rsvp-raid-bot commands :
        # summon -> summon the bot to the current channel if it is not there
        if (words[0] == '<@' + str(client.user.id) + '>'):

            if words[1] == "?":
                # bot, are you here ?
                channels = load(filename)
                is_watching = "not" if message.channel.id not in channels else ""
                reply_msg = "Still here !! And I'm {0} watching this channel.".format(is_watching)
                await message.channel.send(reply_msg)
                return

            if words[1] == "summon":
                await summon_bot(message.channel)
                return

            command = ' '.join([word for word in words[1:]])
            m = re.match(ptrn, command)
            
            if m is not None and is_modo is True:
                # impersonate a user, only works if the author has the "MODO" role
                await impersonate(m.groups()[0], m.groups()[1], message)
                return

            if words[1][:4] == 'here' and message.channel.id in channels:
                session = None
                if re.match(re.compile("here@[0-9]+[hH:][0-9]+"), words[1]) is not None:
                    session = words[1].split('@')[1].replace('H', ':').replace('h', ':')
                extra = ' '.join(words[2:])
                data = load("data/{0}/{1}".format(message.channel.guild.id, message.channel.id))
                players_names = []
                msg = ""
                for s in data["player_list"]:
                    if session is not None and s != session:
                        continue
                    for av in data["player_list"][s]:
                        dec = av.decode('utf8')
                        if dec not in players_names:
                            username = dec.split('#')[0]
                            disc = dec.split('#')[1]

                            u = discord.utils.find(lambda m:m.name == username and m.discriminator == disc, message.guild.members)
                            if u is None:
                                continue
                            
                            msg += u.mention + " "
                            players_names.append(av)

                if len(players_names) > 0:
                    msg += extra 
                    await message.channel.send(msg)
                return

            if words[1] == 'sync':
                if is_sync is True:
                    return

                if is_modo is False:
                    await message.channel.send('Not enough rights to do this action.')
                    return
                
                if message.channel.id not in channels:
                    msg = await summon_bot(message.channel)
                    msgid = msg.id
                else:
                    msgid = channels[message.channel.id]

                await message.delete()
                await message.channel.send('Sync running, please wait.')

#                print('Running sync ({0}/{1})'.format(message.channel.guild.name, message.channel.name))
                
                #Reset file if existing
                channel_data_filepath = "data/{0}/{1}".format(message.channel.guild.id, message.channel.id)
                if os.path.exists(channel_data_filepath):
#                    print('Resetting existing data file')
                    channel_name_base = message.channel.name
                    if channel_name_base.split('-')[0].isdigit() is True:
                        channel_name_base = '-'.join(message.channel.name.split('-')[1:])
                    channel_data = { "player_list": {}, "sessions_list": [], "name": channel_name_base }
#                    print(channel_data)
                    save(channel_data_filepath, channel_data)
                    
                #Read messages posted in chronological order
                async for msg in message.channel.history(limit=250, reverse=True):
#                    print("[0] {1} : {2}".format(msg.id, msg.author.name, msg.content.encode('utf8')))
                    if msg.id != msgid and msg.author.name == 'raid-rsvp-bot':
#                        print('Removing old raid-rsvp-bot message')
                        await msg.delete()
                        continue
                             
                    await process(msg, is_sync = True)
                return

    if message.channel.id not in channels:
        return

    if h.is_message_valid(message_content) is False:
#        print("Invalid message : {0}".format(message_content))
        return

    try:
        await message.add_reaction(u"\u231B") # Hourglass
        answer = await update_list(message, message_content, sender)
        if answer is None:
            return

        msg = await message.channel.get_message(channels[message.channel.id])
        await msg.edit(content = answer)

        # Add a feedback to the message which triggered the bot
        await message.remove_reaction(u"\u231B", message.channel.guild.me)
        await message.add_reaction(u"\u2705") # White check mark

        new_name = get_channel_name_with_participants(message.channel)
        await message.channel.edit(name=new_name)    
    except Exception as inst:
        try:
            with open("/home/tama/error/error.txt", "w", encoding="utf8") as error_txt:
                error_msg = '''
                Oops, `raid-rsvp-bot` got an error :(
                Technical details :
                [[stacktrace]]
                '''
                error_msg = error_msg.replace('[[stacktrace]]', str(inst))
                error_txt.write(error_msg)
        except Exception:
            pass

        print(type(inst))
        print(inst)
        traceback.print_exc()
        await message.remove_reaction(u"\u231B", message.channel.guild.me)


async def impersonate(name, content, message):
    # Treat the message as if the user said the message following the []
    user = discord.utils.find(lambda x : x.name == name, message.channel.guild.members)

    if user is not None:
        await process(message, content, user)

@client.event
async def on_guild_channel_delete(channel):
    h = handlers[channel.guild.id]

    if h.is_disabled() is True:
        print("Bot is disabled on this server")
        return

    if h.should_archive_on_delete() is False:
        print("Archiving is disabled on this server")
        return

    archive_channel_name = h.get_archive_channel_name(channel.name)
    filename = "data/{0}/channels".format(channel.guild.id)
    channels = load(filename)

    if channel.id not in channels:
        return

    # Archive latest message of the bot in this channel in
    # channel #archive
    channel_data = load("data/{0}/{1}".format(channel.guild.id, channel.id))
    player_list = channel_data["player_list"]

    server = channel.guild
    found = None
    for server_channel in server.channels:
        if server_channel.name == archive_channel_name:
            found = server_channel
            break


    message_to_send = '\n**[{0}]**\n{1}'.format(channel.name, get_message(player_list, channel.guild.id, h, False))
    if found is not None:
        await found.send(message_to_send)

    if os.path.exists("data/{0}/archive".format(channel.guild.id)):
        with open("data/{0}/archive".format(channel.guild.id), "r") as f:
            alt_archive_channel_name = f.read()

        found = None
        for server_channel in server.channels:
            if server_channel.name == alt_archive_channel_name:
                found = server_channel
                break

        if found is not None:
            await found.send(message_to_send)

    # Nettoyage
    try:
        del(channels[channel.id])
        os.remove('data/{0}/{1}'.format(channel.guild.id, channel.id))
        save(filename, channels)
    except Exception as e:
        pass

async def update_list(message, message_content, sender):
    # Called when a message posted on a channel triggered the bot
    # Format of valid messages :
    # +[number] pour XX:XX
    # +[number] à XX:XX
    # +[number] pour XXh
    # +[number] à XX:XX
    # +[number] XX:XX
    # -[number] XX:XX

    # Predicates :
    #   The message posted is valid (checked before in on_message)
    #   The bot is already watching the channel on which the message was posted
    channel_data = load("data/{0}/{1}".format(message.channel.guild.id, message.channel.id))
    player_list = channel_data["player_list"]
    sessions_list = channel_data["sessions_list"]
    name = channel_data["name"] if 'name' in channel_data else ''
    player_name = "{0}#{1}".format(sender.name, sender.discriminator)
    player_name = player_name.encode('utf8')
    h = handlers[message.channel.guild.id]
    info = h.parse_message(message, message_content)
    
    userRoles = discord.utils.get(message.guild.members, name=sender.name).roles
    nb = info[0]
    hour = info[1]
    lvs = info[2]
    extra_msg = info[3]
    auto_moved = info[4]
    
    if 'deoxy' in message.channel.name and (auto_moved is True or hour == '00:00'):
        await message.channel.send("Message non pris en compte : l'heure doit être précisée dans les salons des raids EX")
        return
    
    teams_emojis = [':' + h.get_instinct_emoji() + ':', ':' + h.get_mystic_emoji() + ':', ':' + h.get_valor_emoji() + ':']
    teams = []

    player_data = None
    pdata_file = 'data/{0}/player_data'.format(message.channel.guild.id)
    if os.path.exists(pdata_file):
        players_data = load("data/{0}/player_data".format(message.channel.guild.id))
        if player_name in players_data:
            player_data = players_data[player_name]
        
    for te in teams_emojis:
        teams.append(extra_msg.count(te))

    if (player_data is not None) and (nb > 1 and sum(teams) != nb) and sum(player_data) == nb:
        # Check if the player has pre-registered teams
        print('replace {0} {1}'.format(teams, player_data))
        teams = player_data

    p = Player.Player(userRoles, hour, nb, 0, message.content, lvs, extra_msg, teams, h)

    # Invalid time
    if p.from_time is None:
        return None

    # Get the earl>iest available date and look for a session starting around this time
    session = None
    for s in sessions_list:
        if s > p.from_time:
            delta = s - p.from_time
        else:
            delta = p.from_time - s

        if delta.seconds <= max_time_between_sessions:
            session = s
            break

    if session is None:
        session_key = p.from_time.strftime("%H:%M")
        player_list[session_key] = {}
        sessions_list.append(p.from_time)
        if session_key != '00:00':
            await alert_players(message.channel, session_key, player_list)
    else:
        session_key = session.strftime("%H:%M")

    if nb > 0:
        player_list[session_key][player_name] = p

        # Move all "always available players" to this session
        if session_key != "00:00" and "00:00" in player_list:
            available_players = player_list["00:00"]
            for key in available_players:
                p = available_players[key]
                player_list[session_key][key] = p
            player_list["00:00"] = {}
    else:
        # No player is registered for this session, do nothing.
        if player_name not in player_list[session_key]:
            return None

        player_list[session_key][player_name].extra -= -nb
        player_list[session_key][player_name].declined += nb
        if player_list[session_key][player_name].extra <= -1:
            if len(player_list[session_key]) == 1:
                # Last player registered for this session
                sessions_list.remove(player_list[session_key][player_name].from_time)
                del(player_list[session_key][player_name])
                del(player_list[session_key])

                # No session left, create an empty one
                if len(player_list) == 0:
                    player_list['00:00'] = {}
            else:
                # Remove player from session
                del(player_list[session_key][player_name])

    new_data = {"player_list": player_list, "sessions_list": sessions_list, "name": name }
    save("data/{0}/{1}".format(message.channel.guild.id, message.channel.id), new_data)

    answer = get_message_new(message.channel.guild.id, message.channel.id, h)
    if len(answer) > 2000:
        answer = get_message(player_list, message.channel.guild.id, h)
    return answer

async def alert_players(channel, session_key, player_list):
    msg = ''
    for session in player_list:
        for p in player_list[session]:
            dec = p.decode('utf8')
            username = dec.split('#')[0]
            disc = dec.split('#')[1]
            u = discord.utils.find(lambda m:m.name == username and m.discriminator == disc, channel.guild.members)
            if u is None:
                continue
            msg += u.mention + ' '
    msg += ' une nouvelle session a été crée à {0}'.format(session_key)
    await channel.send(msg)

def get_message_new(serverid, channelid, h):
    team_to_emoji = {
        'yellow' : '{0}'.format(get_emoji(h.get_instinct_emoji(), serverid)),
        'red' : '{0}'.format(get_emoji(h.get_valor_emoji(), serverid)),
        'blue': '{0}'.format(get_emoji(h.get_mystic_emoji(), serverid)),
        '?': ':grey_question:'
    }

    ref = [(h.get_instinct_role(), 'yellow'), (h.get_valor_role(), 'red'), (h.get_mystic_role(), 'blue'), ('unknown', '?')]
    c = channelAPI.ChannelAPI("/home/tama/bot", serverid, channelid, ref)
    orderedData = c.read()
    res = ""

    for s in orderedData:
        pnames = set()
        if s != '00:00':
             res += "**```css\n[{0}]\n```**\n".format(s)
        cnt = OrderedDict({'yellow': 0, 'red': 0, 'blue': 0, '?': 0})
        for r in orderedData[s]:
            for p in orderedData[s][r]:
                pname = '#'.join(p[0].split('#')[:-1])
                nb = p[1]
                pdata = p[2]
                
                if nb <= 10:
                    res += nb_to_emoji[nb]
                else:
                    res += '[{0}]'.format(nb)
                    
                res += team_to_emoji[r]
                cnt[r] += nb

                res += " **{0}** ".format(pname)

                for k in team_to_emoji:
                    pdata.extra_msg = pdata.extra_msg.replace(team_to_emoji[k], '')
                pdata.extra_msg = pdata.extra_msg.strip()
                
                if pname not in pnames and len(pdata.extra_msg) > 0:
                    res += "*{0}*".format(pdata.extra_msg)
                    pnames.add(pname)
                res += "\n"

        res += "\n**TOTAL** : "
        for color, nb in sorted(cnt.items(), key = itemgetter(1), reverse = True):
            if nb == 0:
                continue
            res += team_to_emoji[color] + " x **" + str(nb) + "**    "

    #res += "\n" + str(len(res))
    return res
                                          
def get_message(player_list, serverid, h, footer = True, compact = 0):
    team_to_emoji = {}
    team_to_emoji[h.get_instinct_role().lower()] = (':{0}:'.format(h.get_instinct_emoji()), 'instinct')
    team_to_emoji[h.get_valor_role().lower()] = (':{0}:'.format(h.get_valor_emoji()), 'valor')
    team_to_emoji[h.get_mystic_role().lower()] = (':{0}:'.format(h.get_mystic_emoji()), 'mystic')

    answer = 'Players list :\n\n'
    p = 0
    for session in player_list:
        for key in player_list[session]:
            group = player_list[session][key]
            p = p + 1 + group.extra

    for session in player_list:
        player_lvs = {}
        if len(player_list[session]) == 0:
            continue

        if session != '00:00':
            answer += '**```css\n[{0}]\n```**'.format(session)

        available_players = player_list[session]

        player_roles = { "Unknown": 0, "Not sure": 0 }
        count = 0
        for key in available_players:
            dec = key.decode('utf8')
            p = available_players[key]
            player_count = 1 + p.extra
            count += player_count
            player_name = '#'.join(dec.split('#')[:-1])

            if compact == 0 and player_count < 11:
                answer += nb_to_emoji[player_count]
            else:
                answer += '[**{0}**]'.format(player_count)
            answer += " "

            emoji = [
                (get_emoji(h.get_instinct_emoji(), serverid), "[instinct]"),
                (get_emoji(h.get_mystic_emoji(), serverid), "[mystic]"),
                (get_emoji(h.get_valor_emoji(), serverid), "[valor]")   
            ]

            if sum(p.teams) != player_count:
                role = rolestostring(p.roles)
                if len(p.roles) > sum(p.teams):
                    # Prend arbitrairement le premier rôle
                    role = role.split(',')[0]
                    
                if compact == 0 and role in team_to_emoji:
                    # find corresponding emote
                    answer += get_emoji(team_to_emoji[role][0][1:-1], serverid)
                else:
                    if compact == 1:
                        print(key.decode('utf8'))
                        answer += '[{0}]'.format(team_to_emoji[role][0])
                    elif compact == 2:
                        answer += '[{0}]'.format(team_to_emoji[role][0][0])
                    else:
                        answer += "[?]"
            else:
                roles = [
                    h.get_instinct_role(),
                    h.get_mystic_role(),
                    h.get_valor_role()
                ]
                for i, t in enumerate(p.teams):    
                    for j in range(0, t):
                        if compact == 0:
                            answer += emoji[i][0]
                        else:
                            answer += emoji[i][1] 

                    if roles[i].upper() not in player_roles:
                        player_roles[roles[i].upper()] = t
                    else:
                        player_roles[roles[i].upper()] += t

            if 'si ' not in p.extra_msg and 'peut-être' not in p.extra_msg:
                answer += '**'
            answer += "{0}".format(player_name)
            if 'si ' not in p.extra_msg and 'peut-être' not in p.extra_msg:
                answer += '**'
            
            if len(p.lvs) > 0:
                answer += " {0}".format(p.lvs)

            if compact < 2 and p.extra_msg is not None and len(p.extra_msg) > 0:
                for e in emoji:
                    p.extra_msg = p.extra_msg.replace(e[0], e[1])
                answer += " *\"{0}\"*".format(p.extra_msg.strip())
            answer += "\n"

            if player_count > 1:
                if p.declined == 0 and sum(p.teams) != player_count:
                    player_roles["Unknown"] += player_count - 1

            # Player roles
            if p.declined == 0 and sum(p.teams) != player_count:
                for role in p.roles:
                    if role.upper() in player_roles:
                        player_roles[role.upper()] += 1
                    else:
                        player_roles[role.upper()] = 1

                # Player levels, only count if number of levels registered = number of players registered
                # and no one declined afterwards
                if len(p.lvs) == player_count:
                    for lv in p.lvs:
                        if lv not in player_lvs:
                            player_lvs[lv] = 1
                        else:
                            player_lvs[lv] += 1
            elif p.declined > 0:
                player_roles["Not sure"] += player_count

        answer += '\nTOTAL : **{0}** - '.format(count)

        # Player roles
        for r in player_roles:
            if player_roles[r] == 0 and (r == 'Unknown' or r == 'Not sure'):
                continue
            answer += '{0} : {1}   '.format(r, player_roles[r])

        # Player levels
        answer += '\nPlayer levels : '
        for l in player_lvs:
            answer += '{0} x L{1}  '.format(player_lvs[l], l)

        # Line break (end of player list for this session)
        answer += '\n\n'

    # Disclaimer
    if compact == 0 and footer is True:
       answer += '---\n'
       answer += "I'm still learning so I may have missed some messages, if so ping tama\n"
       answer += 'Source code (pull requests welcome) : <https://bitbucket.org/tamati25/pokemon-go-discord-raid-rsvp-bot>'

#    print(len(answer))
    if len(answer) > 2000 and compact < 2:
        return get_message(player_list, serverid, h, footer, compact + 1)
        
    return answer

def get_channel_name_with_participants(channel):
    data_path = "data/{0}/{1}".format(channel.guild.id, channel.id)
    if not os.path.exists(data_path):
        return

    c = channelAPI.ChannelAPI("/home/tama/bot", channel.guild.id, channel.id, None)
    stotal = c.get_total_count()

    first_section = channel.name.split("-")[0]
    if first_section.isdigit():
        keep = "-".join(channel.name.split("-")[1:])
    else:
        keep = channel.name
        
#    unicode_chars = [
#        "\U0001D7EC", # 0
#        "\U0001D7ED", # 1
#        "\U0001D7EE", # 2
#        "\U0001D7EF", # 3
#        "\U0001D7F0", # 4
#        "\U0001D7F1", # 5
#        "\U0001D7F2", # 6
#        "\U0001D7F3", # 7
#        "\U0001D7F4", # 8
#        "\U0001D7F5", # 9
#    ]

    if stotal > 0:
        new_name = "{0}-{1}".format(stotal, keep)
    else:
        new_name = keep
        
    return new_name

def get_emoji(s, serverid):
    for emoji in client.emojis:
        if emoji.name == s and emoji.guild_id == serverid:
            return str(emoji)
    

# -----------------------
# Utils to load/save data
# -----------------------
def save(filename, data):
    pickle.dump(data, open(filename, 'wb'))

def load(filename):
    return pickle.load(open(filename, 'rb'))

def rolestostring(roles):
    ret = ''
    for role in roles:
        ret = ret + ',' + role
    return ret[1:]

if __name__ == '__main__':
    # Load all existing plugins
    plugins = loader.get_plugins("./plugins")
    print(plugins)
    
    for s in os.listdir('data'):
        if not s.isdigit():
            continue

        conffile = 'data/' + s + '/conf'
        conf[int(s)] = { "handler": "default" }
        if os.path.exists(conffile):
            conf_lines = [line.strip() for line in open(conffile, 'r')]
            for line in conf_lines:
                if line.startswith('#'):
                    continue

                key = line.split(':')[0].strip()
                value = line.split(':')[1].strip()
#                print("{0} -> {1}".format(key, value))
                conf[int(s)][key] = value

#        print(conf[s]["handler"])
        handlers[int(s)] = plugins[conf[int(s)]["handler"]]()
                
    token = get_token()
    if token is not None:
        client.run(token)
