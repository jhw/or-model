from scipy.optimize import minimize
from outrights.state import Event

import json, math, random

def mean(X):
    return sum(X) / len(X)

def kernel_1x2(match, ratings, factors, expfn):
    hometeamname, awayteamname = match["name"].split(" vs ")
    homerating = expfn(ratings[hometeamname]) * factors["home_away_bias"]
    awayrating = expfn(ratings[awayteamname]) / factors["home_away_bias"]
    ratio = homerating / (homerating + awayrating)
    drawprob = factors["draw_max"] + factors["draw_curvature"] * (ratio - 0.5) ** 2
    return [ratio * (1 - drawprob),
            drawprob,
            (1 - ratio) * (1 - drawprob)]

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
        probs = [1 / price
                 for price in self.best_prices]
        overround = sum(probs)
        return [prob / overround
                for prob in probs]

class Ratings(dict):

    def __init__(self, teamnames):
        dict.__init__(self)
        for teamname in teamnames:
            self[teamname] = random.gauss(0, 1)

    def normalise(self):
        mn = mean(self.values())
        for key in self.keys():
            self[key] -= mn

class RatingsSolver:

    def rms_error(self, X, Y):
        return (sum([(x - y) ** 2
                     for x, y in zip(X, Y)]) / len(X)) ** 0.5

    def calc_1x2_error(self, matches, ratings, factors):
        probs = [kernel_1x2(match, ratings, factors, math.exp)
                 for match in matches]
        errors = [self.rms_error(prob, Event(match).probabilities)
                  for prob, match in zip(probs,
                                         matches)]
        return sum(errors) / len(matches)

    def optimize_ratings(self, matches, ratings, factors):
        teamnames = list(ratings.keys())
        initial_ratings = [ratings[team] for team in teamnames]

        def objective(rating_vector):
            for i, team in enumerate(teamnames):
                ratings[team] = rating_vector[i]
            ratings.normalise()
            return self.calc_1x2_error(matches, ratings, factors)

        result = minimize(objective, initial_ratings, method='BFGS')
        for i, team in enumerate(teamnames):
            ratings[team] = result.x[i]
        ratings.normalise()
        return ratings

    def optimize_factors(self, matches, ratings, factors):
        factor_keys = list(factors.keys())
        initial_factors = [factors[key] for key in factor_keys]

        def objective(factor_vector):
            for i, key in enumerate(factor_keys):
                factors[key] = factor_vector[i]
            return self.calc_1x2_error(matches, ratings, factors)

        result = minimize(objective, initial_factors, bounds=[(f - 0.1, f + 0.1) for f in initial_factors], method='L-BFGS-B')
        for i, key in enumerate(factor_keys):
            factors[key] = result.x[i]
        return factors

    def solve(self, teamnames, matches, factors):
        ratings = Ratings(teamnames)
        ratings = self.optimize_ratings(matches, ratings, factors)
        factors = self.optimize_factors(matches, ratings, factors)
        ratings = self.optimize_ratings(matches, ratings, factors)
        err = self.calc_1x2_error(matches, ratings, factors)
        return {"ratings": {k:float(v)
                            for k, v in ratings.items()},
                "factors": {k:float(v)
                            for k, v in factors.items()},
                "error": err}

if __name__ == "__main__":
    struct = json.loads(open("tmp/ENG1.json").read())
    teamnames = [team["name"] for team in struct["teams"]]
    trainingset = struct["events"]
    factors = {"home_away_bias": 1.3,
               "draw_max": 0.3,
               "draw_curvature": -0.75}
    resp = RatingsSolver().solve(teamnames=teamnames,
                                 matches=trainingset,
                                 factors=factors)
    print (json.dumps(resp,
                      sort_keys=True,
                      indent=2))
