from model.solver import RatingRange
from model.main import simulate

import json
import pandas as pd
import random

def filter_team_names(events):
    team_names = set()
    for event in events:
        for team_name in event["name"].split(" vs "):
            team_names.add(team_name)
    return sorted(list(team_names))

def normalised_probabilities(prices):
    probs = [1 / price for price in prices]
    overround = sum(probs)
    return [prob / overround for prob in probs]

def market_inputs(event):
    ah_probs = normalised_probabilities(event["asian_handicaps"]["prices"])
    ou_probs = normalised_probabilities(event["over_under_goals"]["prices"])
    return [ah_probs[0], ou_probs[0]]

def model_inputs(event, matrix):
    ah_line = event["asian_handicaps"]["line"]
    ah_probs = matrix.asian_handicaps(ah_line)
    ou_line = event["over_under_goals"]["line"]
    ou_probs = matrix.over_under_goals(ou_line)
    return [ah_probs[0], ou_probs[0]]

if __name__ == "__main__":
    events = json.loads(open("fixtures/ENG1.json").read())
    team_names = filter_team_names(events)
    ratings = {team_name: random.uniform(*RatingRange)
               for team_name in team_names}
    results = [event for event in events
               if event["date"] < "2024-01-01"]
    training_set = sorted(results,
                          key = lambda x: x["date"])[-60:]
    markets = [{"name": "Winner",
                "payoff": "1|19x0"}]
    resp = simulate(ratings = ratings,
                    training_set = training_set,
                    model_selector = lambda event, matrix: model_inputs(event, matrix),
                    market_selector = lambda event: market_inputs(event),
                    results = results,                
                    markets = markets)
    teams = [{"name": team["name"],
              "ppg_rating": team["points_per_game_rating"]}
              for team in resp["teams"]]
    print(pd.DataFrame(sorted(teams,
                              key = lambda x: -x["ppg_rating"])))
    print()
    print(f"Error: {resp['solver_error']:.6f}")
