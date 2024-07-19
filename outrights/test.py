from outrights.state import Event, State
from outrights.helpers import fetch_teams, fetch_events, fetch_results
from outrights.markets import Market, Groups
import outrights.models.simulator as simulator
import outrights.models.solver as solver

SolverParams={"seed": 22682,
              "generations": 250,
              "decay": 2,
              "factors": {"home_away_bias": 1.3,
                          "draw_max": 0.3,
                          "draw_curvature": -0.75}}

SimParams={"seed": 22682,
           "paths": 10000}

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

def filter_training_set(teams, events, limit=6):
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
        raise RuntimeError("no training set")
    return trainingset

"""
leaguename not used but supplied for consistency with init_sim_request
"""

def init_solver_request(leaguename, teams, events, params=SolverParams):
    trainingset=filter_training_set(teams=teams,
                                    events=events)
    return {"teamnames": [team["name"]
                          for team in teams],
            "trainingset": trainingset,
            "params": params}

def init_sim_request(leaguename,
                     ratings,
                     factors,
                     state,
                     markets,
                     params=SimParams,
                     multipliers=DriftMultipliers):
    def init_team(team, ratings):
        modteam=dict(team)
        modteam["rating"]=ratings[team["name"]]
        modteam["goal_diff"]=modteam.pop("goal_difference")
        modteam["live"]=team["live"]
        return modteam
    factors=dict(factors) # NB
    factors["drift_multiplier"]=multipliers[leaguename]
    return {"params": params,
            "factors": factors,
            "teams": [init_team(team, ratings)
                      for team in state["table"]],
            "fixtures": [{"name": fixture}
                         for fixture in state["remaining_fixtures"]],
            "markets": markets}

def generate(leaguename, teams, events, results, markets):
    solver_request=init_solver_request(leaguename=leaguename,
                                       teams=teams,
                                       events=events)
    solver_resp=solver.solve(**solver_request)
    resp={attr:solver_resp[attr]
          for attr in ["ratings",
                       "factors",
                       "error"]}          
    deductions={team["name"]:team["handicap"]
                for team in teams
                if "handicap" in team}
    state=State.initialise(leaguename=leaguename,
                           teams=teams,
                           deductions=deductions,
                           results=results)
    groups=Groups.initialise(markets)
    resp["marks"]=[]
    for groupname, markets in groups.items():
        groupteams=Market(markets[0]).teams(teams)
        state["table"].update_status(groupteams)
        sim_req=init_sim_request(leaguename=leaguename,
                                 ratings=solver_resp["ratings"],
                                 factors=solver_resp["factors"],
                                 state=state,
                                 markets=markets)
        sim_resp=simulator.simulate_marks(**sim_req)
        resp["marks"]+=sim_resp["marks"]
    return resp

Markets=[{"league": "ENG2",
          "name": "Winner",
          "payoff": "1|23x0"}]

if __name__ == "__main__":
    leaguename="ENG2"
    teams=fetch_teams(leaguename)
    events=fetch_events(leaguename)
    results=fetch_results(leaguename)
    markets=[market for market in Markets
             if market["league"]==leaguename]
    resp=generate(leaguename=leaguename,
                  teams=teams,
                  events=events,
                  results=results,
                  markets=markets)
    import json
    print (json.dumps(resp,
                      indent=2))
