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

    def validate_fields(fn):
        def wrapped(self, teams, errors):
            for pat in ["/", "Finish"]:
                if pat in self["name"]:                
                    errors.append("'%s' is invalid name" % self["name"])
            fn(self, teams, errors)
        return wrapped

    @validate_fields
    def validate_include(self, teams, errors):
        teamnames=[team["name"] for team in teams]
        for teamname in self["include"]:
            if teamname not in teamnames:
                errors.append("%s unknown team name '%s'" % (self["name"],
                                                             teamname))
        if len(self.payoff)!=len(self["include"]):
            errors.append("%s has incorrect payoff length" % self["name"])

    @validate_fields
    def validate_exclude(self, teams, errors):
        teamnames=[team["name"] for team in teams]
        for teamname in self["exclude"]:
            if teamname not in teamnames:
                errors.append("%s unknown team name '%s'" % (self["name"],
                                                                 teamname))                                  
        if len(self.payoff)!=len(teamnames)-len(self["exclude"]):
            errors.append("%s has incorrect payoff length" % self["name"])

    @validate_fields
    def validate_default(self, teams, errors):
        if len(self.payoff)!=len(teams):
            errors.append("%s has incorrect payoff length" % self["name"])
            
    def validate(self, teams, errors):
        if "include" in self:
            self.validate_include(teams, errors)
        elif "exclude" in self:
            self.validate_exclude(teams, errors)
        else:
            self.validate_default(teams, errors)

class Markets(list):

    def __init__(self, items=[]):
        list.__init__(self, items)

    def validate(self, leaguename, teams):
        errors=[]
        for market in self:
            market.validate(teams, errors)
        if errors!=[]:
            raise RuntimeError("%s market errors - %s" % (leaguename,
                                                          ", ".join(errors)))
        
if __name__=="__main__":
    pass
