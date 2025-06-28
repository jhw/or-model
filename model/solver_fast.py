from model.kernel import ScoreMatrix
import numpy as np
import math
import logging
import random

RatingRange = (0, 6)
HomeAdvantageRange = (1, 1.5)

class OptimizationResult:
    def __init__(self, x, fun, success=True):
        self.x = x
        self.fun = fun
        self.success = success

def minimize_fast(objective, x0, bounds=None, options=None):
    """Fast genetic algorithm optimization with mutations - based on original v0.0.1 solver"""
    if options is None:
        options = {}
    
    max_iter = options.get('maxiter', 100)
    decay = options.get('decay', 2.0)
    mutation_factor = options.get('mutation_factor', 0.1)
    logger = logging.getLogger(__name__)
    
    x = np.array(x0, dtype=float)
    best_fun = objective(x)
    
    logger.info(f"Starting fast genetic optimization with {max_iter} generations")
    logger.debug(f"Initial objective value: {best_fun:.6f}")
    
    for generation in range(max_iter):
        old_fun = best_fun
        decay_factor = ((max_iter - generation) / max_iter) ** decay
        
        # Log progress every 10th generation
        if generation % 10 == 0 or generation == max_iter - 1:
            logger.info(f"Generation {generation + 1}/{max_iter}: objective={best_fun:.6f}, decay={decay_factor:.4f}")
        
        # Mutate each parameter
        for i in range(len(x)):
            delta = random.gauss(0, 1) * decay_factor * mutation_factor
            
            # Try positive mutation
            x[i] += delta
            if bounds and bounds[i]:
                low, high = bounds[i]
                x[i] = max(low, min(high, x[i]))  # Clamp to bounds
            
            new_fun = objective(x)
            if new_fun < best_fun:
                best_fun = new_fun
                continue
            
            # Try negative mutation
            x[i] -= 2 * delta
            if bounds and bounds[i]:
                low, high = bounds[i]
                x[i] = max(low, min(high, x[i]))  # Clamp to bounds
            
            new_fun = objective(x)
            if new_fun < best_fun:
                best_fun = new_fun
                continue
            
            # Reset if no improvement
            x[i] += delta
        
        # Early convergence check
        if abs(old_fun - best_fun) < 1e-6:
            logger.info(f"Converged at generation {generation + 1}")
            break
    
    logger.info(f"Fast optimization completed. Final objective value: {best_fun:.6f}")
    return OptimizationResult(x, best_fun)

def minimize_hybrid(objective, x0, bounds=None, options=None):
    """Hybrid approach: fast genetic for coarse optimization, then coordinate descent for fine-tuning"""
    if options is None:
        options = {}
    
    max_iter = options.get('maxiter', 100)
    logger = logging.getLogger(__name__)
    
    # Phase 1: Fast genetic algorithm (80% of iterations)
    genetic_iter = int(max_iter * 0.8)
    genetic_options = {'maxiter': genetic_iter, 'decay': 2.0, 'mutation_factor': 0.1}
    result1 = minimize_fast(objective, x0, bounds, genetic_options)
    
    # Phase 2: Coordinate descent for fine-tuning (20% of iterations)
    fine_iter = max_iter - genetic_iter
    fine_options = {'maxiter': fine_iter}
    
    logger.info(f"Switching to coordinate descent for fine-tuning ({fine_iter} iterations)")
    
    x = result1.x
    best_fun = result1.fun
    learning_rate = 0.01
    tolerance = 1e-6
    
    for iteration in range(fine_iter):
        old_fun = best_fun
        
        # Coordinate descent
        for i in range(len(x)):
            for direction in [-1, 1]:
                step = learning_rate * direction
                
                if bounds and bounds[i]:
                    low, high = bounds[i]
                    new_val = x[i] + step
                    if new_val < low or new_val > high:
                        continue
                
                x[i] += step
                new_fun = objective(x)
                
                if new_fun < best_fun:
                    best_fun = new_fun
                    break
                else:
                    x[i] -= step
        
        # Check convergence
        if abs(old_fun - best_fun) < tolerance:
            logger.info(f"Fine-tuning converged at iteration {iteration + 1}")
            break
        
        # Adaptive learning rate
        if best_fun < old_fun:
            learning_rate *= 1.01
        else:
            learning_rate *= 0.99
    
    logger.info(f"Hybrid optimization completed. Final objective value: {best_fun:.6f}")
    return OptimizationResult(x, best_fun)

class RatingsSolver:

    def __init__(self, model_selector, market_selector, fast_mode=True):
        self.model_selector = model_selector
        self.market_selector = market_selector
        self.fast_mode = fast_mode
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
        method = "fast genetic" if self.fast_mode else "hybrid"
        self.logger.info(f"Starting ratings optimization ({method}) for {len(ratings)} teams with fixed home advantage {home_advantage}")
        
        team_names = sorted(list(ratings.keys()))
        optimiser_ratings = [ratings[team_name] for team_name in team_names]
        optimiser_bounds = [rating_range] * len(optimiser_ratings)

        def objective(params):
            for i, team in enumerate(team_names):
                ratings[team] = params[i]
            return self.calc_error(events = events,
                                   ratings = ratings,
                                   home_advantage = home_advantage)

        minimize_func = minimize_fast if self.fast_mode else minimize_hybrid
        result = minimize_func(objective,
                              optimiser_ratings,
                              bounds = optimiser_bounds,
                              options = {'maxiter': max_iterations})
        
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        self.logger.info(f"Ratings optimization completed with final error: {result.fun:.6f}")

    def optimise_ratings_and_bias(self, events, ratings, max_iterations,
                                  rating_range = RatingRange,
                                  bias_range = HomeAdvantageRange):
        method = "fast genetic" if self.fast_mode else "hybrid"
        self.logger.info(f"Starting joint optimization ({method}) of {len(ratings)} team ratings and home advantage")
        
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

        minimize_func = minimize_fast if self.fast_mode else minimize_hybrid
        result = minimize_func(objective,
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
        method = "fast genetic" if self.fast_mode else "hybrid"
        self.logger.info(f"Starting solver ({method}) with {len(events)} events, max_iterations={max_iterations}")
        
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