DefaultGroup="Default"

class Groups(dict):

    @classmethod
    def initialise(self, markets):
        groups={}
        for market in markets:
            groupname=market["name"] if ("include" in market or
                                         "exclude" in market) else DefaultGroup
            groups.setdefault(groupname, [])
            groups[groupname].append(market)
        return Groups(groups)

    def __init__(self, items={}):
        dict.__init__(self, items)

class Market(dict):

    def __init__(self, item={}):
        dict.__init__(self, item)

    @property
    def group(self):
        return self["name"] if ("include" in self or
                                "exclude" in self) else DefaultGroup

    @property
    def payoff(self):
        payoff=[]
        for expr in self["payoff"].split("|"):
            tokens=[float(tok) # allow championship playoffs 0.25
                    for tok in expr.split("x")]
            # why can't assignment code below be done in single line ??
            if len(tokens)==1:            
                n, v = 1, tokens[0]
            else:
                n, v = tokens
            for i in range(int(n)):
                payoff.append(v)
        return payoff
    
    def teams(self, teams):
        teammap={team["name"]:team
                 for team in teams}
        if "include" in self:
            return [teammap[teamname]
                    for teamname in self["include"]]
        elif "exclude" in self:
            return [teammap[team["name"]]
                    for team in teams
                    if team["name"] not in self["exclude"]]
        else:
            return teams

if __name__=="__main__":
    pass
