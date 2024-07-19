from model.state import Event, Result, Results, State

from model.markets import Market, Markets, Groups

import model.simulator as simulator

import model.solver as solver

import copy, json, urllib.request

DriftMultipliers={
    "ENG1": 0.005,
    "ENG2": 0.01,
    "ENG3": 0.015,
    "ENG4": 0.02,
    "FRA1": 0.005,
    "FRA2": 0.01,
    "GER1": 0.005,
    "GER2": 0.01,
    "ITA1": 0.005,
    "ITA2": 0.01,
    "NED1": 0.005,
    "SCO2": 0.01,
    "SCO3": 0.015,
    "SCO4": 0.02,
    "SPA1": 0.005,
    "SPA2": 0.01
}

SolverParams={"seed": 22682,
              "generations": 250,
              "decay": 2,
              "factors": {"home_away_bias": 1.3,
                          "draw_max": 0.3,
                          "draw_curvature": -0.75}}

SimParams={"seed": 22682,
           "paths": 10000}

def fetch_teams(leaguename,
                domainname="outrights.net"):
    url="https://teams.%s/list-teams?league=%s" % (domainname,
                                                   leaguename)
    return json.loads(urllib.request.urlopen(url).read())
    
def fetch_events(leaguename,
                 domainname="outrights.net"):
    url="https://events.%s/list-events?league=%s" % (domainname,
                                                     leaguename)
    return [Event(event)
            for event in json.loads(urllib.request.urlopen(url).read())]
    
def filter_training_set(leaguename, teams, events, limit=6):
    class Counter(dict):
        def __init__(self, teams):
            dict.__init__(self, {team["name"]:0
                                 for team in teams})
        def add(self, event):
            for teamname in event["name"].split(" vs "):
                self[teamname]+=1
        def is_complete(self, limit):
            for k, v in self.items():
                if v < limit:
                    return False
            return True
    counter, trainingset = Counter(teams), []
    for event in reversed(sorted(events,
                                 key=lambda x: "%s/%s" % (x["date"],
                                                          x["name"]))):
        trainingset.append(event)
        counter.add(event)
        if counter.is_complete(limit):
            return trainingset
    if trainingset==[]:
        raise RuntimeError("%s no training set" % leaguename)
    return trainingset

def init_sim_request(league, ratings, state, markets, params):
    def init_team(team, ratings):
        modteam=copy.deepcopy(team)
        modteam["rating"]=ratings[team["name"]]
        modteam["goal_diff"]=modteam.pop("goal_difference")
        modteam["live"]=team["live"]
        return modteam
    def init_teams(ratings, state):
        return [init_team(team, ratings["ratings"])
               for team in state["table"]]
    def init_fixtures(state):
        return [{"name": fixture}
                for fixture in state["remaining_fixtures"]]
    def init_markets(markets):
        return [{"name": market["name"],
                 "payoff": market["payoff"]}
                for market in markets]
    def init_factors(league, ratings):
        modfactors=copy.deepcopy(ratings["factors"])
        modfactors["drift_multiplier"]=league["drift_multiplier"]
        return modfactors
    teams=init_teams(ratings, state)
    fixtures=init_fixtures(state)
    markets=init_markets(markets)
    factors=init_factors(league, ratings)
    return {"params": params,
            "factors": factors,
            "teams": teams,
            "fixtures": fixtures,
            "markets": markets}

if __name__ == "__main__":
    leaguename="ENG2"
    teams, events = (fetch_teams(leaguename),
                     fetch_events(leaguename))
    trainingset=filter_training_set(leaguename=leaguename,
                                    teams=teams,
                                    events=events)
    solver_request={"teamnames": [team["name"]
                                  for team in teams],
                    "trainingset": trainingset,
                    "params": SolverParams}
    solver_resp=solver.solve(**solver_request)
    print (solver_resp["ratings"])
    print (solver_resp["factors"])
    print (solver_resp["error"])
    deductions={}
    results=[]
    state=State.initialise(leaguename=leaguename,
                           teams=teams,
                           deductions=deductions,
                           results=Results([Result(result)
                                            for result in results]))
    state.validate(leaguename, teams)
    allmarkets=[{"league": "ENG2",
                 "name": "Winner",
                 "payoff": "1|23x0"}]
    markets=Markets([Market(market)
                     for market in allmarkets
                     if market["league"]==leaguename])
    markets.validate(leaguename, teams)
    groups=Groups.initialise(markets)
    marks=[]
    for groupname, markets in groups.items():
        groupteams=markets[0].teams(teams)
        state["table"].update_status(groupteams)
        league={"drift_multiplier": DriftMultipliers[leaguename]}
        simreq=init_sim_request(league=league,
                                ratings=solver_resp,
                                state=state,
                                markets=markets,
                                params=SimParams)
        simresp=simulator.simulate_marks(**simreq)
        marks+=simresp["marks"]
    print (marks)
