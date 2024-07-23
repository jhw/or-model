from scipy.optimize import minimize
from scipy.special import factorial
import json
import math
import random
import sys
import re
import numpy as np

def poisson_prob(lmbda, k):
    return (lmbda ** k) * np.exp(-lmbda) / factorial(k)

def dixon_coles_adjustment(i, j, rho):
    if i == 0 and j == 0:
        return 1 - (i * j * rho)
    elif i == 0 and j == 1:
        return 1 + (rho / 2)
    elif i == 1 and j == 0:
        return 1 + (rho / 2)
    elif i == 1 and j == 1:
        return 1 - rho
    else:
        return 1

def kernel_poisson(match, ratings, rho=0.1, home_advantage=1.2):
    hometeamname, awayteamname = match["name"].split(" vs ")
    home_lambda = ratings[hometeamname] * home_advantage
    away_lambda = ratings[awayteamname]

    home_goals = np.arange(11)
    away_goals = np.arange(11)

    home_probs = poisson_prob(home_lambda, home_goals[:, np.newaxis])
    away_probs = poisson_prob(away_lambda, away_goals[np.newaxis, :])
    
    dixon_coles_matrix = np.vectorize(dixon_coles_adjustment)(home_goals[:, np.newaxis], away_goals[np.newaxis, :], rho)
    score_matrix = home_probs * away_probs * dixon_coles_matrix

    home_win_prob = np.sum(np.tril(score_matrix, -1))
    draw_prob = np.sum(np.diag(score_matrix))
    away_win_prob = np.sum(np.triu(score_matrix, 1))

    return [home_win_prob, draw_prob, away_win_prob]

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
        probs = [1 / price for price in self.best_prices]
        overround = sum(probs)
        return [prob / overround for prob in probs]

class Ratings(dict):
    def __init__(self, teamnames):
        dict.__init__(self)
        for teamname in teamnames:
            self[teamname] = random.uniform(0, 6)

class RatingsSolver:
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def calc_poisson_error(self, matches, ratings, rho=0.1, home_advantage=1.2):
        probs = [kernel_poisson(match, ratings, rho, home_advantage) for match in matches]
        errors = [self.rms_error(prob, Event(match).probabilities) for prob, match in zip(probs, matches)]
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
            return self.calc_poisson_error(matches, ratings, rho, home_advantage)

        result = minimize(objective, initial_params, method='L-BFGS-B', bounds=bounds, options={'maxiter': 100})
        for i, team in enumerate(teamnames):
            ratings[team] = result.x[i]
        home_advantage = result.x[-1]
        return ratings, home_advantage

    def solve(self, teamnames, matches, rho=0.1):
        ratings = Ratings(teamnames)
        ratings, home_advantage = self.optimize_ratings_and_bias(matches, ratings, rho)
        err = self.calc_poisson_error(matches, ratings, rho, home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": home_advantage,
                "error": err}

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter n(events)")
        n_events = sys.argv[1]
        if not re.search("^\\d+$", n_events):
            raise RuntimeError("n(events) is invalid")
        n_events = int(n_events)
        struct = json.loads(open("dev/solver-data.json").read())
        teamnames = [team["name"] for team in struct["teams"]]
        trainingset = list(reversed(sorted(struct["events"],
                                           key = lambda e: e["date"])))[:n_events]
        rho = 0.1  # Dixon-Coles adjustment parameter
        resp = RatingsSolver().solve(teamnames=teamnames, matches=trainingset, rho=rho)
        print(json.dumps(resp, sort_keys=True, indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
