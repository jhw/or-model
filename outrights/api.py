from outrights.markets import Market, Groups
from outrights.state import State
import outrights.models.simulator as simulator
import outrights.models.solver as solver

SolverParams={"generations": 250,
              "decay": 2,
              "factors": {"home_away_bias": 1.3,
                          "draw_max": 0.3,
                          "draw_curvature": -0.75}}

SimParams={"paths": 10000}

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

def init_solver_request(teams, events, params=SolverParams):
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
    factors["drift_multiplier"]=multipliers[leaguename]
    return {"params": params,
            "factors": factors,
            "teams": [init_team(team, ratings)
                      for team in state["table"]],
            "fixtures": [{"name": fixture}
                         for fixture in state["remaining_fixtures"]],
            "markets": markets}

def generate(leaguename, teams, events, results, markets):
    resp={}
    solver_request=init_solver_request(teams=teams,
                                       events=events)
    resp["training_set"]=solver_request["trainingset"]
    solver_resp=solver.solve(**solver_request)    
    resp.update({attr:solver_resp[attr]
                 for attr in ["ratings",
                              "ppg_ratings",
                              "factors",
                              "error"]})
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

if __name__=="__main__":
    pass
