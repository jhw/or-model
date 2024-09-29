from model.solver import RatingRange
from model.main import simulate

import json
import random

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
                    model_selector = lambda event: event.match_odds,
                    market_selector = lambda event: filter_1x2_probabilities(event),
                    results = results,
                    markets = markets)
    print(json.dumps(resp, indent = 2))
