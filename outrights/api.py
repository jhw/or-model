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

def mean(X):
    return sum(X)/len(X) if X != [] else 0

def variance(X):
    m=mean(X)
    return sum([(x-m)**2 for x in X])

def filter_training_set(teams, events, limit=6):
    class Counter(dict):
        def __init__(self, teams):
            dict.__init__(self, {team["name"]:0
                                 for team in teams})
        def shall_add(self, event):
            for teamname in event["name"].split(" vs "):
                if self[teamname] >= limit:
                    return False
            return True
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
                                 key=lambda x: x["date"])):
        if counter.shall_add(event):
            trainingset.append(event)
            counter.add(event)
        if counter.is_complete(limit):
            break
    if trainingset==[]:
        raise RuntimeError("training set is empty")
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

def format_table(teams, results, deductions, solver_req, solver_resp):
    table=[{"name": team["name"],
            "normal_rating": solver_resp["ratings"][team["name"]],
            "ppg_rating": solver_resp["ppg_ratings"][team["name"]],
            "points": 0 if team["name"] not in deductions else deductions[team["name"]],
            "played": 0,
            "expected_points": 0,
            "n_training_events": len(solver_resp["training_sets"][team["name"]]),
            "mean_error": mean([event["error"]
                                for event in solver_resp["training_sets"][team["name"]]]),
            "var_error": variance([event["error"]
                                   for event in solver_resp["training_sets"][team["name"]]])}
           for team in teams]
    table={team["name"]:team
           for team in table}
    for result in results:
        hometeamname, awayteamname = result["name"].split(" vs ")
        homegoals, awaygoals = [int(tok) for tok in result["score"].split("-")]
        if homegoals > awaygoals:
            table[hometeamname]["points"]+=3
        elif homehoals < awaygoals:
            table[awayteamname]["points"]+=3
        else:
            table[hometeamname]["points"]+=1
            table[awayteamname]["points"]+=1
        table[hometeamname]["played"]+=1
        table[awayteamname]["played"]+=1
    for team in table.values():
        team["expected_points"]+=team["points"]
    for fixture in solver_resp["fixtures"]:
        hometeamname, awayteamname = fixture["name"].split(" vs ")
        homewinprob, drawprob, awaywinprob = fixture["probabilities"]
        table[hometeamname]["expected_points"]+=3*homewinprob+drawprob
        table[awayteamname]["expected_points"]+=3*awaywinprob+drawprob
    return list(table.values())

def format_metrics(solver_resp):
    metrics=solver_resp["factors"]
    metrics["error"]=solver_resp["error"]
    return metrics
    
def generate(leaguename, teams, events, results, markets):
    deductions={team["name"]:team["handicap"]
                for team in teams
                if "handicap" in team}

    solver_req=init_solver_request(teams=teams,
                                       events=events)
    solver_resp=solver.solve(**solver_req)
    table=format_table(teams=teams,                    
                       results=results,
                       deductions=deductions,
                       solver_req=solver_req,
                       solver_resp=solver_resp)
    metrics=format_metrics(solver_resp)
    state=State.initialise(leaguename=leaguename,
                           teams=teams,
                           deductions=deductions,
                           results=results)
    groups=Groups.initialise(markets)
    marks=[]
    for groupname, markets in groups.items():
        groupteams=Market(markets[0]).teams(teams)
        state["table"].update_status(groupteams)
        sim_req=init_sim_request(leaguename=leaguename,
                                 ratings=solver_resp["ratings"],
                                 factors=solver_resp["factors"],
                                 state=state,
                                 markets=markets)
        sim_resp=simulator.simulate_marks(**sim_req)
        marks+=sim_resp["marks"]
    return {"table": table,
            "metrics": metrics,
            "marks": marks}


if __name__=="__main__":
    pass
