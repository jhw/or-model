from model.kernel import ScoreMatrix
from scipy.optimize import minimize
import numpy as np
import random

RatingRange = (0, 6)
HomeAdvantageRange = (1, 1.5)

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
    def expected_home_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[0] + match_odds[1]

    @property
    def expected_away_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[2] + match_odds[1]

def init_ratings(fn, rating_range = RatingRange):
    def wrapped(self, *args, **kwargs):
        if (("ratings" not in kwargs or
            not kwargs["ratings"]) and
            ("team_names" not in kwargs or
             not kwargs["team_names"])):
            raise RuntimeError("please specify either ratings or team_names")
        if ("team_names" in kwargs and
            kwargs["team_names"]):
            kwargs["ratings"] = {team_name: random.uniform(*rating_range)
                                 for team_name in kwargs.pop("team_names")}
        return fn(self, *args, **kwargs)
    return wrapped
            
class RatingsSolver:

    def __init__(self, selector_fn = lambda x: getattr(x, "match_odds")):
        self.selector_fn = selector_fn
    
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def calc_error(self, events, ratings, home_advantage):
        matrices = [ScoreMatrix.initialise(event_name = event["name"],
                                           ratings = ratings,
                                           home_advantage = home_advantage)
                    for event in events]        
        errors = [self.rms_error(self.selector_fn(matrix),
                                 self.selector_fn(Event(event)))
                  for event, matrix in zip(events, matrices)]
        return np.mean(errors)

    @init_ratings
    def optimise_ratings_only(self, events, ratings, home_advantage, max_iterations,
                              rating_range = RatingRange,
                              **kwargs):
        team_names = sorted(list(ratings.keys()))
        
        optimiser_ratings = [ratings[team_name] for team_name in team_names]
        optimiser_bounds = [rating_range] * len(optimiser_ratings)

        def objective(params):
            for i, team in enumerate(team_names):
                ratings[team] = params[i]
            return self.calc_error(events = events,
                                   ratings = ratings,
                                   home_advantage = home_advantage)

        result = minimize(objective,
                          optimiser_ratings,
                          method = 'L-BFGS-B',
                          bounds = optimiser_bounds,
                          options = {'maxiter': max_iterations})
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        return ratings

    @init_ratings
    def optimise_ratings_and_bias(self, events, ratings, max_iterations,
                                  rating_range = RatingRange,
                                  bias_range = HomeAdvantageRange,
                                  **kwargs):
        team_names = sorted(list(ratings.keys()))

        optimiser_ratings = [ratings[team_name] for team_name in team_names]
        optimiser_bias = sum(bias_range) / 2
        optimiser_bounds = [rating_range] * len(optimiser_ratings) + [bias_range]
        optimiser_params = optimiser_ratings + [optimiser_bias]

        def objective(params):
            for i, team in enumerate(team_names):
                ratings[team] = params[i]
            home_advantage = params[-1]
            return self.calc_error(events = events,
                                   ratings = ratings,
                                   home_advantage = home_advantage)

        result = minimize(objective,
                          optimiser_params,
                          method = 'L-BFGS-B',
                          bounds = optimiser_bounds,
                          options = {'maxiter': max_iterations})
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        home_advantage = result.x[-1]        
        return ratings, home_advantage

    """
    Pass initial guess ratings to solver or have it randomise them based on team names if guesses not available
    """
    
    def solve(self, events,
              team_names = None,
              ratings = None,
              home_advantage = None,
              max_iterations = 100):
        if home_advantage:
            ratings = self.optimise_ratings_only(events = events,
                                                 team_names = team_names,
                                                 ratings = ratings,
                                                 home_advantage = home_advantage,
                                                 max_iterations = max_iterations)
        else:
            ratings, home_advantage = self.optimise_ratings_and_bias(events = events,
                                                                     team_names = team_names,
                                                                     ratings = ratings,
                                                                     max_iterations = max_iterations)
        error = self.calc_error(events = events,
                                ratings = ratings,
                                home_advantage = home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": float(home_advantage),
                "error": float(error)}

if __name__=="__main__":
    pass
