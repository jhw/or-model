#!/usr/bin/env python3

import time
import logging
import json
import random
from model.solver_fast import RatingsSolver as FastSolver

# Configure detailed logging to see iterations
logging.basicConfig(
    level=logging.INFO,
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

def main():
    league_name = "ENG1"
    file_name = f"fixtures/{league_name}.json"
    
    with open(file_name, 'r') as f:
        results = json.load(f)
    
    team_names = filter_team_names(results)
    training_set = sorted(results, key=lambda x: x["date"])[-3*len(team_names):]
    
    print(f"Testing Fast Solver with detailed logging")
    print(f"League: {league_name}")
    print(f"Teams: {len(team_names)}")
    print(f"Training events: {len(training_set)}")
    
    # Create starting ratings
    random.seed(42)
    ratings = {team_name: random.uniform(0, 6) for team_name in team_names}
    
    start_time = time.time()
    
    solver = FastSolver(
        model_selector=lambda event, matrix: matrix.match_odds,
        market_selector=lambda event: filter_1x2_probabilities(event),
        fast_mode=True  # Use pure genetic algorithm
    )
    
    result = solver.solve(
        events=training_set,
        ratings=ratings.copy(),
        max_iterations=100
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\nFinal Results:")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Final error: {result['error']:.6f}")
    print(f"Home advantage: {result['home_advantage']:.6f}")
    
    # Show top rated teams
    sorted_ratings = sorted(result['ratings'].items(), key=lambda x: x[1], reverse=True)
    print(f"\nTop 5 rated teams:")
    for i, (team, rating) in enumerate(sorted_ratings[:5]):
        print(f"{i+1}. {team}: {rating:.3f}")

if __name__ == "__main__":
    main()