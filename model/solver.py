from model.kernel import ScoreMatrix
import numpy as np
import math

RatingRange = (0, 6)
HomeAdvantageRange = (1, 1.5)

class OptimizationResult:
    def __init__(self, x, fun, success=True):
        self.x = x
        self.fun = fun
        self.success = success

def minimize(objective, x0, bounds=None, options=None):
    """Simple gradient-free optimization using coordinate descent with random restarts"""
    if options is None:
        options = {}
    
    max_iter = options.get('maxiter', 100)
    learning_rate = 0.01
    tolerance = 1e-6
    
    x = np.array(x0, dtype=float)
    best_x = x.copy()
    best_fun = objective(x)
    
    # Multiple random restarts for better global optimization
    for restart in range(3):
        if restart > 0:
            # Random restart within bounds
            if bounds:
                for i in range(len(x)):
                    low, high = bounds[i]
                    x[i] = np.random.uniform(low, high)
            else:
                x = np.array(x0) + np.random.normal(0, 0.1, len(x0))
        
        current_fun = objective(x)
        
        for iteration in range(max_iter):
            old_fun = current_fun
            
            # Coordinate descent with adaptive step size
            for i in range(len(x)):
                # Try both directions
                for direction in [-1, 1]:
                    step = learning_rate * direction
                    
                    # Apply bounds if specified
                    if bounds and bounds[i]:
                        low, high = bounds[i]
                        new_val = x[i] + step
                        if new_val < low or new_val > high:
                            continue
                    
                    # Test the step
                    x[i] += step
                    new_fun = objective(x)
                    
                    if new_fun < current_fun:
                        current_fun = new_fun
                        break
                    else:
                        x[i] -= step  # Revert step
            
            # Check for convergence
            if abs(old_fun - current_fun) < tolerance:
                break
            
            # Adaptive learning rate
            if current_fun < old_fun:
                learning_rate *= 1.01  # Increase if improving
            else:
                learning_rate *= 0.99  # Decrease if not improving
        
        # Keep best result across restarts
        if current_fun < best_fun:
            best_fun = current_fun
            best_x = x.copy()
    
    return OptimizationResult(best_x, best_fun)


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
