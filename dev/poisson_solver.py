from scipy.optimize import minimize
import numpy as np
import random
from poisson_common import ScoreMatrix

# Event Class
class Event(dict):
    def __init__(self, event):
        dict.__init__(self, event)

    def probabilities(self, attr):
        probs = [1 / price for price in self[attr]["prices"]]
        overround = sum(probs)
        return [prob / overround for prob in probs]

    @property
    def match_odds(self):
        return self.probabilities("match_odds")

    @property
    def training_inputs(self):
        return self.match_odds

# Ratings Class
class Ratings(dict):
    def __init__(self, teamnames):
        dict.__init__(self)
        for teamname in teamnames:
            self[teamname] = random.uniform(0, 6)

# RatingsSolver Class
class RatingsSolver:
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def calc_error(self, matches, ratings, rho=0.1, home_advantage=1.2):
        matrices = [ScoreMatrix.initialise(match, ratings, rho, home_advantage) for match in matches]        
        errors = [self.rms_error(matrix.training_inputs, match.training_inputs) for matrix, match in zip(matrices, matches)]
        return np.mean(errors)

    def optimize_ratings_and_bias(self, matches, ratings, rho=0.1):
        teamnames = list(ratings.keys())
        initial_ratings = [ratings[team] for team in teamnames]
        initial_params = initial_ratings + [1.2]  # Start with home_advantage of 1.2
        bounds = [(0, 6)] * len(initial_ratings) + [(1, 1.5)]

        def objective(params):
            for i, team in enumerate(teamnames):
                ratings[team] = params[i]
            home_advantage = params[-1]
            return self.calc_error(matches, ratings, rho, home_advantage)

        result = minimize(objective, initial_params, method='L-BFGS-B', bounds=bounds, options={'maxiter': 100})
        for i, team in enumerate(teamnames):
            ratings[team] = result.x[i]
        home_advantage = result.x[-1]
        return ratings, home_advantage

    def solve(self, teamnames, matches, rho=0.1):
        ratings = Ratings(teamnames)
        ratings, home_advantage = self.optimize_ratings_and_bias(matches, ratings, rho)
        err = self.calc_error(matches, ratings, rho, home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": home_advantage,
                "error": err}

def filter_teamnames(events):
    teamnames = set()
    for event in events:
        for teamname in event["name"].split(" vs "):
            teamnames.add(teamname)
    return sorted(list(teamnames))

if __name__=="__main__":
    try:
        import json, re, sys, urllib.request
        if len(sys.argv) < 4:
            raise RuntimeError("please enter league, cutoff, n_events")
        leaguename, cutoff, n_events = sys.argv[1:4]
        if not re.search("^\\D{3}\\d$", leaguename):
            raise RuntimeError("league is invalid")
        if not re.search("^\\d{4}\\-\\d{2}\\-\\d{2}$", cutoff):
            raise RuntimeError("cutoff is invalid")
        if not re.search("^\\d+$", n_events):
            raise RuntimeError("n_events is invalid")
        n_events = int(n_events)
        print ("fetching leagues")
        leagues={league["name"]: league
                for league in json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        from fd_scraper import fetch_events
        print ("fetching events")
        events = [Event(event)
                  for event in fetch_events(leagues[leaguename])
                  if event["date"] <= cutoff]
        if events == []:
            raise RuntimeError("no events found")
        print ("%i events" % len(events))
        teamnames = filter_teamnames(events)
        trainingset = list(reversed(sorted(events,
                                           key = lambda e: e["date"])))[:n_events]
        print ("training set %s -> %s [%i]" % (trainingset[-1]["date"],
                                               trainingset[0]["date"],
                                               len(trainingset)))
        rho = 0.1  # Dixon-Coles adjustment parameter
        resp = RatingsSolver().solve(teamnames=teamnames, matches=trainingset, rho=rho)
        print ()
        print(json.dumps(resp, sort_keys=True, indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
