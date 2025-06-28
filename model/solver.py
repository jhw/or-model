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

def minimize(objective, x0, bounds=None, options=None):
    """Enhanced genetic algorithm with multi-start initialization and periodic exploration"""
    if options is None:
        options = {}
    
    max_iter = options.get('maxiter', 100)
    decay = options.get('decay', 1.0)
    mutation_factor = options.get('mutation_factor', 0.08)  # Larger mutations to prevent premature convergence
    n_random_starts = options.get('n_random_starts', 20)  # Number of random starting points
    logger = logging.getLogger(__name__)
    
    # Phase 1: Find best starting point from multiple random starts
    logger.info(f"Testing {n_random_starts} random starting points to find best initialization")
    
    best_start_x = np.array(x0, dtype=float)
    best_start_fun = objective(best_start_x)
    
    for start_idx in range(n_random_starts):
        # Generate random starting point within bounds
        if bounds:
            random_x = np.array([np.random.uniform(low, high) for low, high in bounds])
        else:
            # More diverse starting points
            random_x = np.array(x0) + np.random.normal(0, 1.0, len(x0))
            
        random_fun = objective(random_x)
        
        if random_fun < best_start_fun:
            best_start_fun = random_fun
            best_start_x = random_x.copy()
            logger.debug(f"New best start found at trial {start_idx + 1}: {random_fun:.6f}")
    
    logger.info(f"Best starting point found with objective: {best_start_fun:.6f}")
    
    # Phase 2: Genetic algorithm optimization with periodic wide random exploration
    x = best_start_x
    best_fun = best_start_fun
    exploration_interval = options.get('exploration_interval', 100)  # Wide random every N generations
    n_exploration_points = options.get('n_exploration_points', 15)  # Points to test during exploration
    
    logger.info(f"Starting genetic optimization with {max_iter} generations (wide random every {exploration_interval} generations)")
    
    for generation in range(max_iter):
        old_fun = best_fun
        decay_factor = ((max_iter - generation) / max_iter) ** decay
        
        # Log progress every 50th generation for longer runs
        if generation % 50 == 0 or generation == max_iter - 1:
            logger.info(f"Generation {generation + 1}/{max_iter}: objective={best_fun:.6f}, decay={decay_factor:.4f}")
        
        # Periodic wide random exploration to escape local optima
        if generation > 0 and generation % exploration_interval == 0:
            logger.info(f"Wide random exploration at generation {generation + 1} (testing {n_exploration_points} points)")
            exploration_best_x = x.copy()
            exploration_best_fun = best_fun
            
            for explore_idx in range(n_exploration_points):
                # Generate diverse exploration point
                if bounds:
                    explore_x = np.array([np.random.uniform(low, high) for low, high in bounds])
                else:
                    explore_x = x + np.random.normal(0, 1.5, len(x))  # Large variance for exploration
                
                explore_fun = objective(explore_x)
                if explore_fun < exploration_best_fun:
                    exploration_best_x = explore_x.copy()
                    exploration_best_fun = explore_fun
                    logger.debug(f"Better point found during exploration: {explore_fun:.6f}")
            
            # Use exploration result if it's better
            if exploration_best_fun < best_fun:
                x = exploration_best_x
                best_fun = exploration_best_fun
                logger.info(f"Jumped to better solution from exploration: {best_fun:.6f}")
        
        # Regular genetic mutations
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
        
        # Dynamic convergence check - stricter tolerance as we progress
        # Early generations: allow more exploration, later generations: require precision
        convergence_tolerance = 1e-8 if generation > max_iter * 0.5 else 1e-10
        if abs(old_fun - best_fun) < convergence_tolerance and generation > 50:
            logger.info(f"Converged at generation {generation + 1} (tolerance={convergence_tolerance})")
            break
    
    logger.info(f"Optimization completed. Final objective value: {best_fun:.6f}")
    return OptimizationResult(x, best_fun)


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
              max_iterations = 500):
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