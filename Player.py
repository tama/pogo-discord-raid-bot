from dateutil import parser

class Player:
    def __init__(self, roles, from_time, extra, declined, message, lvs, extra_msg, teams, h):
        self.message = message
        self.from_time = self.format_time(from_time)
        self.extra = extra - 1
        self.extra_msg = extra_msg
        # players who accepted but declined later
        self.declined = 0
        self.lvs = lvs
        self.teams = teams
        self.valid_roles = [h.get_instinct_role().lower(), h.get_valor_role().lower(), h.get_mystic_role().lower()]
        self.roles = self.filter_roles(roles)
        
    def filter_roles(self, roles):
        filtered = []
        for role in roles:
            if role.name.lower() in self.valid_roles:
                filtered.append(role.name.lower())
        return filtered

    def format_time(self, time):
        if time is None:
            return None

        if time.find(":") > -1:
            sep = ':'
        elif time.find('H') > -1:
            sep = 'H'
        else:
            sep = 'h'
            
        hm = time.split(sep)

        if len(hm[0]) < 2:
            hm[0] = '0' + hm[0]
            
        if int(hm[0]) < 0 or int(hm[0]) > 23:
            return None
        if len(hm) > 1 and len(hm[1]) == 2:
            if int(hm[1]) < 0 or int(hm[1]) > 59:
                return None

        if len(hm) < 2 or len(hm[1]) < 2:
            full_date = "20170906T" + hm[0] + '0000'
        else:
            full_date = "20170906T" + hm[0] + hm[1] + '00'

        return parser.parse(full_date)

    def __str__(self):
        return("extra: {0}, declined: {1}, lvs : {2}, extra_msg: {3}".format(self.extra, self.declined, self.lvs, self.extra_msg))
