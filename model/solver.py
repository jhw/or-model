from model.kernel import ScoreMatrix
from scipy.optimize import minimize
import numpy as np

RatingRange = (0, 6)
HomeAdvantageRange = (1, 1.5)


class RatingsSolver:

    def __init__(self, model_selector, market_selector):
        self.model_selector = model_selector
        self.market_selector = market_selector
    
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def calc_error(self, events, ratings, home_advantage):
        matrices = [ScoreMatrix.initialise(event_name = event["name"],
                                           ratings = ratings,
                                           home_advantage = home_advantage)
                    for event in events]        
        errors = [self.rms_error(self.model_selector(event = event,
                                                     matrix = matrix),
                                 self.market_selector(event))
                  for event, matrix in zip(events, matrices)]
        return np.mean(errors)

    def optimise_ratings(self, events, ratings, home_advantage, max_iterations,
                         rating_range = RatingRange):
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

    def optimise_ratings_and_bias(self, events, ratings, max_iterations,
                                  rating_range = RatingRange,
                                  bias_range = HomeAdvantageRange):
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
        return result.x[-1]        

    def solve(self, events, ratings,
              home_advantage = None,
              max_iterations = 100):
        if home_advantage:
            self.optimise_ratings(events = events,
                                  ratings = ratings,
                                  home_advantage = home_advantage,
                                  max_iterations = max_iterations)
        else:
            home_advantage = self.optimise_ratings_and_bias(events = events,
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
