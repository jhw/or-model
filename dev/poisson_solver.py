from poisson_common import Event
from poisson_kernel import ScoreMatrix
from scipy.optimize import minimize
import numpy as np
import random

# Ratings Class
class Ratings(dict):
    def __init__(self, team_names):
        dict.__init__(self)
        for team_name in team_names:
            self[team_name] = random.uniform(0, 6)

# RatingsSolver Class
class RatingsSolver:
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def calc_error(self, matches, ratings, home_advantage):
        matrices = [ScoreMatrix.initialise(event_name = match["name"],
                                           ratings = ratings,
                                           home_advantage = home_advantage)
                    for match in matches]        
        errors = [self.rms_error(matrix.training_inputs,
                                 match.training_inputs)
                  for matrix, match in zip(matrices, matches)]
        return np.mean(errors)

    def optimize_ratings_and_bias(self, matches, ratings, home_advantage=1.2):
        team_names = list(ratings.keys())
        initial_ratings = [ratings[team_name] for team_name in team_names]
        initial_params = initial_ratings + [home_advantage]
        bounds = [(0, 6)] * len(initial_ratings) + [(1, 1.5)]

        def objective(params):
            for i, team in enumerate(team_names):
                ratings[team] = params[i]
            home_advantage = params[-1]
            return self.calc_error(matches, ratings, home_advantage)

        result = minimize(objective,
                          initial_params,
                          method='L-BFGS-B',
                          bounds=bounds,
                          options={'maxiter': 100})
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        home_advantage = result.x[-1]
        return ratings, home_advantage

    def solve(self, team_names, matches):
        ratings = Ratings(team_names)
        ratings, home_advantage = self.optimize_ratings_and_bias(matches, ratings)
        err = self.calc_error(matches, ratings, home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": float(home_advantage),
                "error": float(err)}

if __name__=="__main__":
    pass
