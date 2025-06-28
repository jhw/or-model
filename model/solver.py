from model.kernel import ScoreMatrix
from model.state import calc_league_table
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
    """Parallel genetic algorithm with population-based optimization"""
    if options is None:
        options = {}
    
    max_iter = options.get('maxiter', 50)  # Fewer generations since we run more candidates per generation
    population_size = options.get('population_size', 8)  # Parallel candidates per generation
    mutation_factor = options.get('mutation_factor', 0.1)
    elite_ratio = options.get('elite_ratio', 0.2)  # Top 20% survive to next generation
    logger = logging.getLogger(__name__)
    
    n_params = len(x0)
    n_elite = max(1, int(population_size * elite_ratio))
    
    logger.info(f"Starting parallel genetic algorithm: {max_iter} generations, {population_size} candidates per generation")
    
    # Initialize population - shape: (population_size, n_params)
    population = []
    
    # First candidate: use league table-sorted initial guess (x0)
    population.append(np.array(x0, dtype=float))
    
    # Remaining candidates: random within bounds
    for _ in range(population_size - 1):
        if bounds:
            candidate = np.array([np.random.uniform(low, high) for low, high in bounds])
        else:
            candidate = np.array(x0) + np.random.normal(0, 1.0, n_params)
        population.append(candidate)
    
    population = np.array(population)
    
    best_fitness = float('inf')
    best_solution = None
    
    for generation in range(max_iter):
        # Evaluate all candidates in parallel
        fitness_scores = np.array([objective(individual) for individual in population])
        
        # Find best solution
        best_idx = np.argmin(fitness_scores)
        if fitness_scores[best_idx] < best_fitness:
            best_fitness = fitness_scores[best_idx]
            best_solution = population[best_idx].copy()
        
        # Log progress
        if generation % 10 == 0 or generation == max_iter - 1:
            avg_fitness = np.mean(fitness_scores)
            time_remaining = (max_iter - generation) / max_iter
            current_mutation = mutation_factor * (time_remaining ** 0.5)
            logger.info(f"Generation {generation + 1}/{max_iter}: best={best_fitness:.6f}, avg={avg_fitness:.6f}, mutation={current_mutation:.4f}")
        
        # Check convergence
        excellent_error = options.get('excellent_error', 0.03)
        max_error = options.get('max_error', 0.05)
        
        if best_fitness <= excellent_error:
            logger.info(f"Excellent result achieved at generation {generation + 1}: error {best_fitness:.6f} ≤ {excellent_error}")
            break
            
        if best_fitness > max_error and generation == max_iter - 1:
            logger.warning(f"Max generations reached with error {best_fitness:.6f} > {max_error}")
        
        # Selection: keep elite performers
        elite_indices = np.argsort(fitness_scores)[:n_elite]
        elite_population = population[elite_indices]
        
        # Generate new population
        new_population = []
        
        # Keep elite unchanged
        for i in range(n_elite):
            new_population.append(elite_population[i].copy())
        
        # Calculate decay factor for this generation
        time_remaining = (max_iter - generation) / max_iter  # Goes from 1.0 to 0.0
        decay_factor = time_remaining ** 0.5  # Square root decay
        current_mutation_factor = mutation_factor * decay_factor
        
        # Generate offspring from elite
        while len(new_population) < population_size:
            # Select random elite parent
            parent_idx = np.random.randint(0, n_elite)
            parent = elite_population[parent_idx].copy()
            
            # Apply mutations with decay
            for i in range(n_params):
                if np.random.random() < 0.3:  # 30% mutation probability per parameter
                    mutation = np.random.normal(0, current_mutation_factor)
                    parent[i] += mutation
                    
                    # Clamp to bounds
                    if bounds and bounds[i]:
                        low, high = bounds[i]
                        parent[i] = max(low, min(high, parent[i]))
            
            new_population.append(parent)
        
        population = np.array(new_population)
    
    logger.info(f"Parallel optimization completed. Final objective value: {best_fitness:.6f}")
    return OptimizationResult(best_solution, best_fitness)


class RatingsSolver:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def initialize_ratings_from_league_table(self, team_names, results, rating_range=(0, 6)):
        """Initialize team ratings based on league table points using existing calc_league_table"""
        # Use existing league table calculation
        league_table = calc_league_table(team_names, results, handicaps={})
        
        # If no results available, use random initialization
        if not league_table or all(team['points'] == 0 for team in league_table):
            self.logger.info("No match results found, using random initialization")
            return {team: random.uniform(*rating_range) for team in team_names}
        
        # Map league position to rating range
        min_rating, max_rating = rating_range
        rating_span = max_rating - min_rating
        
        # Distribute ratings based on league position (already sorted by points + goal difference)
        ratings = {}
        for i, team_data in enumerate(league_table):
            # Linear mapping: best team gets max rating, worst gets min rating
            position_ratio = i / (len(league_table) - 1) if len(league_table) > 1 else 0
            rating = max_rating - (position_ratio * rating_span)
            ratings[team_data['name']] = rating
            
        top_team = league_table[0]
        self.logger.info(f"Initialized ratings from league table: {top_team['name']} ({top_team['points']} pts) = {ratings[top_team['name']]:.2f}")
        return ratings
    
    def rms_error(self, X, Y):
        return np.sqrt(np.mean((np.array(X) - np.array(Y)) ** 2))

    def extract_market_probabilities(self, event):
        """Extract normalized probabilities from match odds prices"""
        prices = event["match_odds"]["prices"]
        probs = [1 / price for price in prices]
        overround = sum(probs)
        return [prob / overround for prob in probs]
    
    def calc_error(self, events, ratings, home_advantage):
        """Calculate RMS error for single ratings configuration"""
        matrices = [ScoreMatrix.initialise(event_name = event["name"],
                                           ratings = ratings,
                                           home_advantage = home_advantage)
                    for event in events]        
        errors = [self.rms_error(matrix.match_odds,
                                 self.extract_market_probabilities(event))
                  for event, matrix in zip(events, matrices)]
        return np.mean(errors)

    def optimise_ratings(self, events, ratings, home_advantage, options,
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
                         options = options)
        
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        self.logger.info(f"Ratings optimization completed with final error: {result.fun:.6f}")

    def optimise_ratings_and_bias(self, events, ratings, options,
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
                         options = options)
        
        for i, team in enumerate(team_names):
            ratings[team] = result.x[i]
        home_advantage = result.x[-1]
        self.logger.info(f"Joint optimization completed with final error: {result.fun:.6f}, home advantage: {home_advantage:.6f}")
        return home_advantage        

    def solve(self, events, ratings,
              home_advantage = None,
              max_iterations = 500,
              exploration_interval = 50,
              n_exploration_points = 10,
              excellent_error = 0.03,
              max_error = 0.05,
              use_league_table_init = True,
              results = []):
        self.logger.info(f"Starting solver with {len(events)} events, max_iterations={max_iterations}")
        
        # Optionally initialize ratings from league table instead of using provided ratings
        if use_league_table_init and results:
            team_names = sorted(list(ratings.keys()))
            league_table_ratings = self.initialize_ratings_from_league_table(team_names, results)
            ratings.update(league_table_ratings)  # Update the provided ratings dict
        
        optimization_options = {
            'maxiter': max_iterations,
            'exploration_interval': exploration_interval,
            'n_exploration_points': n_exploration_points,
            'excellent_error': excellent_error,
            'max_error': max_error
        }
        
        if home_advantage:
            self.optimise_ratings(events = events,
                                  ratings = ratings,
                                  home_advantage = home_advantage,
                                  options = optimization_options)
        else:
            home_advantage = self.optimise_ratings_and_bias(events = events,
                                                            ratings = ratings,
                                                            options = optimization_options)
        error = self.calc_error(events = events,
                                ratings = ratings,
                                home_advantage = home_advantage)
        
        self.logger.info(f"Solver completed with final error: {error:.6f}")
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": float(home_advantage),
                "error": float(error)}

if __name__=="__main__":
    pass