from model.kernel import ScoreMatrix
import numpy as np
import math
import logging

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
    logger = logging.getLogger(__name__)
    
    x = np.array(x0, dtype=float)
    best_x = x.copy()
    best_fun = objective(x)
    
    # Multiple random restarts for better global optimization
    for restart in range(3):
        logger.info(f"Starting optimization restart {restart + 1}/3")
        if restart > 0:
            # Random restart within bounds
            if bounds:
                for i in range(len(x)):
                    low, high = bounds[i]
                    x[i] = np.random.uniform(low, high)
            else:
                x = np.array(x0) + np.random.normal(0, 0.1, len(x0))
        
        current_fun = objective(x)
        logger.debug(f"Restart {restart + 1} initial objective value: {current_fun:.6f}")
        
        for iteration in range(max_iter):
            old_fun = current_fun
            
            # Log every 10th iteration or first/last iterations
            if iteration % 10 == 0 or iteration == max_iter - 1:
                logger.info(f"Restart {restart + 1} iteration {iteration + 1}/{max_iter}: objective={current_fun:.6f}, lr={learning_rate:.6f}")
            
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
                logger.info(f"Restart {restart + 1} converged at iteration {iteration + 1} (tolerance={tolerance})")
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
            logger.debug(f"New best result from restart {restart + 1}: {best_fun:.6f}")
    
    logger.info(f"Optimization completed. Best objective value: {best_fun:.6f}")
    return OptimizationResult(best_x, best_fun)


class RatingsSolver:

    def __init__(self, model_selector, market_selector):
        self.model_selector = model_selector
        self.market_selector = market_selector
        self.logger = logging.getLogger(__name__)
    
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
        self.logger.info(f"Starting ratings optimization for {len(ratings)} teams with fixed home advantage {home_advantage}")
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
        self.logger.info(f"Ratings optimization completed with final error: {result.fun:.6f}")

    def optimise_ratings_and_bias(self, events, ratings, max_iterations,
                                  rating_range = RatingRange,
                                  bias_range = HomeAdvantageRange):
        self.logger.info(f"Starting joint optimization of {len(ratings)} team ratings and home advantage")
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
        home_advantage = result.x[-1]
        self.logger.info(f"Joint optimization completed with final error: {result.fun:.6f}, home advantage: {home_advantage:.6f}")
        return home_advantage        

    def solve(self, events, ratings,
              home_advantage = None,
              max_iterations = 100):
        self.logger.info(f"Starting solver with {len(events)} events, max_iterations={max_iterations}")
        
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
        
        self.logger.info(f"Solver completed with final error: {error:.6f}")
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": float(home_advantage),
                "error": float(error)}

if __name__=="__main__":
    pass
