from model.state import Result, Results, State

from model.markets import Market, Markets, Groups

import model.simulator as simulator

import copy, json, os, urllib.request

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

SimParams={"seed": 22682,
           "paths": 10000}

def fetch_teams(leaguename,
                 domainname="outrights.net"):
    url="https://teams.%s/list-teams?league=%s" % (domainname,
                                                   leaguename)
    return json.loads(urllib.request.urlopen(url).read())

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
    params=SimParams
    driftmultipliers=DriftMultipliers
    teams, deductions = (fetch_teams(leaguename), {})
    def init_results(results):
        return Results([Result(result)
                        for result in results])
    results=init_results([])
    state=State.initialise(leaguename=leaguename,
                           teams=teams,
                           deductions=deductions,
                           results=results)
    state.validate(leaguename, teams)
    ratings={
        "ratings": {
            "Blackburn": -0.2947580837731432,
            "Bristol City": -0.4854565205933645,
            "Burnley": 1.8551391542498676,
            "Cardiff": -0.9433556160227132,
            "Coventry": -0.13769257302350726,
            "Derby": -0.2504512997707219,
            "Hull": -0.04381537490473129,
            "Leeds": 1.189810958488093,
            "Luton": 1.245348955441433, # manually tweaked
            "Middlesbrough": 0.05787725491426396,
            "Millwall": -0.6508381469056274,
            "Norwich": 0.28408264559076696,
            "Oxford": -0.42571338563576894,
            "Plymouth": -0.7962569230992319,
            "Portsmouth": -0.1556893175728399,
            "Preston": -0.7695992246990699,
            "QPR": -0.27455613754060504,
            "Sheffield Utd": -0.177289477437231,
            "Sheffield Weds": -0.4982355217878988,
            "Stoke": -0.2597038358726272,
            "Sunderland": -0.4909097488482811,
            "Swansea": -0.4582666402060736,
            "Watford": -0.5719227871710468,
            "West Brom": 0.0522516461800584
        },
        "factors": {
            "home_away_bias": 1.1996634009194602,
            "draw_max": 0.29102084765665415,
            "draw_curvature": -0.8564836281252888
        }        
    }
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
        league={"drift_multiplier": driftmultipliers[leaguename]}
        simreq=init_sim_request(league=league,
                                ratings=ratings,
                                state=state,
                                markets=markets,
                                params=params)
        simresp=simulator.simulate_marks(**simreq)
        marks+=simresp["marks"]
    print (marks)
