from outrights.markets import Market

from outrights.models import kernel_1x2

import numpy.random as npr
import numpy as np

def node_value(item, gdmult=1e-4, noisemult=1e-8):
    value=item[0]
    value+=gdmult*item[1]
    value+=npr.uniform(low=-noisemult, high=noisemult)
    return value

def simulate_points(teams, fixtures, factors, paths, overrides={}):
    def array(value):
        return np.ones(paths, 'd')*value
    points={team["name"]:[array(team["points"]), array(team["goal_diff"])]
            for team in teams
            if team["live"]}
    ratings={team["name"]:array(team["rating"])
             for team in teams}
    for fixture in fixtures:
        # expectations
        if fixture["name"] in overrides:
            probs=overrides[fixture["name"]]
        else:
            probs=kernel_1x2(fixture, ratings, factors, np.exp)
        exphomepts=3*probs[0]+probs[1]
        expawaypts=3*probs[2]+probs[1]
        # results
        q=npr.uniform(size=paths)
        homewin=np.array(q < probs[0], 'i')
        awaywin=np.array(q > (1-probs[2]), 'i')
        draw=(1-homewin)*(1-awaywin)
        homepts=3*homewin+draw        
        awaypts=3*awaywin+draw
        homegd=homewin-awaywin # single goal only
        awaygd=awaywin-homewin # single goal only
        # drift
        homedelta=homepts-exphomepts
        awaydelta=awaypts-expawaypts
        homedrift=homedelta*factors["drift_multiplier"]
        awaydrift=awaydelta*factors["drift_multiplier"]
        # update
        hometeamname, awayteamname = fixture["name"].split(" vs ")
        if hometeamname in points:
            points[hometeamname][0]+=homepts
            points[hometeamname][1]+=homegd
            ratings[hometeamname]+=homedrift
        if awayteamname in points:
            points[awayteamname][0]+=awaypts
            points[awayteamname][1]+=awaygd
            ratings[awayteamname]+=awaydrift
    points={teamname:node_value(q)
            for teamname, q in points.items()}
    return points, ratings

def calc_position_probs(teams, points, paths):
    liveteams=[team for team in teams
               if team["live"]]
    pp={team["name"]: [0 for i in range(len(liveteams))]
        for team in liveteams}
    pathval=1/paths
    for i in range(paths):
        table=sorted([(key, pts[i])
                      for key, pts in points.items()],
                     key=lambda x: -x[-1])
        for j, team in enumerate(table):
            name, pts = team
            pp[name][j]+=pathval
    return pp

def sumproduct(X, Y):
    return sum([x*y for x, y in zip(X, Y)])

def calc_marks(markets, teams, pp):
    marks=[]
    for _market in markets:
        market=Market(_market)
        for team in teams:
            if not team["live"]:
                continue
            mark={"market": market["name"],
                  "team": team["name"],
                  "mark": sumproduct(market.payoff,
                                     pp[team["name"]])}
            marks.append(mark)
    return marks

def simulate_marks(params, markets, teams, fixtures, factors, overrides={}):
    simpoints, ratings = simulate_points(teams,
                                         sorted(fixtures,
                                                key=lambda x: x["name"]),
                                         factors,
                                         params["paths"],
                                         overrides)
    pp=calc_position_probs(teams, simpoints, params["paths"])
    marks=calc_marks(markets, teams, pp)
    def stats(array):
        return {"mean": np.mean(array),
                "stdev": np.std(array),
                "min": np.min(array),
                "max": np.max(array)}
    return {"matrix": pp,
            "marks": marks,
            "ratings": {key:stats(values)
                        for key, values in ratings.items()}}

if __name__=="__main__":
    import json, yaml
    request=json.loads(open("fixtures/model/marks/simulator.json").read())
    resp=simulate_marks(**request)
    print (yaml.safe_dump(sorted([mark for mark in resp["marks"]
                                  if (mark["market"]=="Winner" and
                                      mark["mark"] > 0.01)],
                                 key=lambda x: -x["mark"]),
                          default_flow_style=False))
