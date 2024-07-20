class Event(dict):

    def __init__(self, event):
        dict.__init__(self, event)

    @property
    def best_prices(self, sources="fd|oc".split("|")):
        for source in sources:
            if source in self["prices"]:
                return self["prices"][source]
        return None
        
    @property
    def probabilities(self):                      
        probs=[1/price
               for price in self.best_prices]
        overround=sum(probs)
        return [prob/overround
                for prob in probs]

class Result(dict):

    def __init__(self, result):
        dict.__init__(self, result)

    @property
    def score(self, sources="fd|bbc|tf".split("|")):
        for source in sources:
            if source in self["scores"]:
                return self["scores"][source]
        raise RuntimeError("score not found in %s :: %s" % (self["name"],
                                                            self["scores"]))

class Results(list):

    def __init__(self, results=[]):
        list.__init__(self, results)

    def remaining_fixtures(self, teams, rounds):
        class Count(dict):
            @classmethod
            def initialise(self, teams, rounds):
                teamnames=[team["name"]
                           for team in teams]
                items={}
                for hometeamname in teamnames:
                    for awayteamname in teamnames:
                        if hometeamname!=awayteamname:
                            key="%s vs %s" % (hometeamname,
                                              awayteamname)
                            items[key]=rounds
                return Count(items)
            def __init__(self, items={}):
                dict.__init__(self, items)
            def decrement(self, result):
                self[result["name"]]-=1
            def expand(self):
                fixtures=[]
                for key, value in self.items():
                    for i in range(value):
                        fixtures.append(key)
                return fixtures
        count=Count.initialise(teams, rounds)
        for result in self:
            count.decrement(result)
        return count.expand()
        
class Table(list):

    @classmethod
    def initialise(self, teams, deductions):
        def points_for(team, deductions):
            return 0 if team["name"] not in deductions else -abs(deductions[team["name"]])
        return Table([{"name": team["name"],
                       "points": points_for(team, deductions),
                       "played": 0,
                       "goal_difference": 0}
                      for team in teams])

    def __init__(self, items=[]):
        list.__init__(self, items)
        self.teamnames=[item["name"]
                        for item in items]
        
    def update_result(self, result):
        hometeamname, awayteamname = result["name"].split(" vs ")
        homegoals, awaygoals = [int(goals)
                                for goals in Result(result).score.split("-")]
        if hometeamname in self.teamnames:
            i=self.teamnames.index(hometeamname)
            hometeam=self[i]
            hometeam.update(homegoals, awaygoals)
        if awayteamname in self.teamnames:
            i=self.teamnames.index(awayteamname)
            awayteam=self[i]
            awayteam.update(awaygoals, homegoals)

    def update_results(self, results):
        for result in results:
            self.update_result(result)

    def update_status(self, groupteams):
        teamnames=[team["name"]
                   for team in groupteams]
        for team in self:
            team["live"]=team["name"] in teamnames

class State(dict):

    @classmethod
    def rounds_for(self, leaguename):
        return 2 if "SCO" in leaguename else 1
    
    @classmethod
    def initialise(self, leaguename, teams, deductions, results):
        rounds=State.rounds_for(leaguename)
        leaguetable=Table.initialise(teams=teams,
                                     deductions=deductions)
        leaguetable.update_results(results)
        remfixtures=Results(results).remaining_fixtures(teams=teams,
                                                        rounds=rounds)
        return State({"table": leaguetable,
                      "remaining_fixtures": remfixtures})

    def __init__(self, item={}):
        dict.__init__(self, item)

if __name__=="__main__":
    pass