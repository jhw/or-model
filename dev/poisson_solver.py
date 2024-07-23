from scipy.optimize import minimize
from scipy.special import factorial
import json
import math
import random
import numpy as np

def mean(X):
    return np.mean(X)

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

    def optimize_ratings(self, matches, ratings, rho=0.1, home_advantage=1.2):
        teamnames = list(ratings.keys())
        initial_ratings = [ratings[team] for team in teamnames]

        def objective(rating_vector):
            for i, team in enumerate(teamnames):
                ratings[team] = rating_vector[i]
            return self.calc_poisson_error(matches, ratings, rho, home_advantage)

        result = minimize(objective, initial_ratings, method='BFGS', options={'maxiter': 100})
        for i, team in enumerate(teamnames):
            ratings[team] = result.x[i]
        return ratings

    def solve(self, teamnames, matches, rho=0.1, home_advantage=1.2):
        ratings = Ratings(teamnames)
        ratings = self.optimize_ratings(matches, ratings, rho, home_advantage)
        err = self.calc_poisson_error(matches, ratings, rho, home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "error": err}

if __name__ == "__main__":
    struct = json.loads(open("tmp/ENG1.json").read())
    teamnames = [team["name"] for team in struct["teams"]]
    trainingset = struct["events"]
    rho = 0.1  # Dixon-Coles adjustment parameter
    home_advantage = 1.2  # Home advantage multiplier
    resp = RatingsSolver().solve(teamnames=teamnames, matches=trainingset, rho=rho, home_advantage=home_advantage)
    print(json.dumps(resp, sort_keys=True, indent=2))
