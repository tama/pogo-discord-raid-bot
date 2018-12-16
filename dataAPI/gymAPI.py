#!/usr/bin/env python3

class GymAPI:
    def __init__(self, basepath, servid):
        self.servid = servid
        self.path = "{0}/data/{1}/{2}".format(basepath, servid)
        self.reload()

    def reload(self):
        if not os.path.exists(self.path):
            print("Gym data not found")
            return
        
        raw_data = [line.strip() for line in open(self.path, "r", encoding="utf8")]
        self.data = []
        for l in raw_data:
            try:
                sections = l.split(";")
                is_ex_gym = (sections[-1] == "EX")
                self.data.append((sections[0], sections[1], sections[2], sections[3], sections[4], is_ex_gym))
            except Exception as e:
                print("Failed to load gym data ({0})".format(l))
                print(str(e))

    def get_infos(self, shortName):
        m = [g for g in self.data if g[0] == shortName]
        if len(m) > 0:
            return m[0]
        return None

    def get_category(self, shortName):
        category = "{0}/data/{1}/category".format(servid)
        if not os.path.exists(category):
            return None
        catdata = [line.strip() for line in open(category, "r", encoding="utf8")]
        m = [x for x in catdata if x.split(':')[1] == shortName]
        if len(m) > 0:
            return m[0].split(':')[0]
        return None
    
    def get_gym_around(self, shortName, radius):
        
        pass

    
