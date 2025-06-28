#!/usr/bin/env python3

import time
import logging
import json
import sys
import random
from model.solver import RatingsSolver as SlowSolver
from model.solver_fast import RatingsSolver as FastSolver
from model.main import simulate

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise for benchmarking
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def filter_team_names(events):
    team_names = set()
    for event in events:
        for team_name in event["name"].split(" vs "):
            team_names.add(team_name)
    return sorted(list(team_names))

def filter_1x2_probabilities(event):
    probs = [1 / price for price in event["match_odds"]["prices"]]
    overround = sum(probs)
    return [prob / overround for prob in probs]

def benchmark_solver(solver_class, solver_name, ratings, training_set, max_iterations=50):
    print(f"\n=== Benchmarking {solver_name} ===")
    
    start_time = time.time()
    
    solver = solver_class(
        model_selector=lambda event, matrix: matrix.match_odds,
        market_selector=lambda event: filter_1x2_probabilities(event)
    )
    
    # Make a copy of ratings to avoid interference
    test_ratings = ratings.copy()
    
    result = solver.solve(
        events=training_set,
        ratings=test_ratings,
        max_iterations=max_iterations
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Duration: {duration:.2f} seconds")
    print(f"Final error: {result['error']:.6f}")
    print(f"Home advantage: {result['home_advantage']:.6f}")
    
    return duration, result['error']

def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_solvers.py <league_code>")
        print("Example: python benchmark_solvers.py ENG1")
        return
    
    league_name = sys.argv[1]
    file_name = f"fixtures/{league_name}.json"
    
    try:
        with open(file_name, 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_name} not found")
        return
    
    team_names = filter_team_names(results)
    training_set = sorted(results, key=lambda x: x["date"])[-3*len(team_names):]
    
    print(f"League: {league_name}")
    print(f"Teams: {len(team_names)}")
    print(f"Training events: {len(training_set)}")
    
    # Create identical starting ratings for fair comparison
    random.seed(42)  # Fixed seed for reproducible results
    ratings = {team_name: random.uniform(0, 6) for team_name in team_names}
    
    max_iterations = 50  # Reduced for faster benchmarking
    
    # Benchmark current slow solver
    slow_time, slow_error = benchmark_solver(
        SlowSolver, "Current Solver (Coordinate Descent)", 
        ratings, training_set, max_iterations
    )
    
    # Benchmark fast genetic solver
    fast_time, fast_error = benchmark_solver(
        lambda *args, **kwargs: FastSolver(*args, **kwargs, fast_mode=True),
        "Fast Solver (Genetic Algorithm)",
        ratings, training_set, max_iterations
    )
    
    # Benchmark hybrid solver
    hybrid_time, hybrid_error = benchmark_solver(
        lambda *args, **kwargs: FastSolver(*args, **kwargs, fast_mode=False),
        "Hybrid Solver (Genetic + Coordinate Descent)",
        ratings, training_set, max_iterations
    )
    
    print(f"\n=== COMPARISON SUMMARY ===")
    print(f"Current Solver:  {slow_time:.2f}s, error: {slow_error:.6f}")
    print(f"Fast Solver:     {fast_time:.2f}s, error: {fast_error:.6f} ({fast_time/slow_time:.1f}x faster)")
    print(f"Hybrid Solver:   {hybrid_time:.2f}s, error: {hybrid_error:.6f} ({hybrid_time/slow_time:.1f}x faster)")
    
    speedup_fast = slow_time / fast_time
    speedup_hybrid = slow_time / hybrid_time
    
    print(f"\nSpeedup: Fast {speedup_fast:.1f}x, Hybrid {speedup_hybrid:.1f}x")

if __name__ == "__main__":
    main()