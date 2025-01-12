from model.solver import RatingRange
from model.main import simulate

import json
import os
import random
import re
import sys
import yaml

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
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        league_name = sys.argv[1]
        if not re.search("^\\D{3}\\d{1}", league_name):
            raise RuntimeError("league is invalid")
        file_name = f"fixtures/{league_name}.json"
        if not os.path.exists(file_name):
            raise RuntimeError(f"{file_name} does not exist")
        results = json.loads(open(file_name).read())
        team_names = filter_team_names(results)
        ratings = {team_name: random.uniform(*RatingRange)
                   for team_name in team_names}
        training_set = sorted(results,
                              key = lambda x: x["date"])[-3*len(team_names):]
        winner_payoff = f"1|{len(team_names)-1}x0"
        markets = [{"name": "Winner",
                    "payoff": winner_payoff}]
        rounds = 2 if "SCO" in league_name else 1
        resp = simulate(ratings = ratings,
                        training_set = training_set,
                        model_selector = lambda event, matrix: matrix.match_odds,
                        market_selector = lambda event: filter_1x2_probabilities(event),
                        results = results,
                        markets = markets,
                        rounds = rounds)
        print(yaml.safe_dump(sorted([{"name": team["name"],
                                      "points": team["points"],
                                      "ppg_rating": team["points_per_game_rating"]}
                                     for team in resp["teams"]],
                                    key = lambda x: -x["ppg_rating"]),
                             default_flow_style = False))
        print(yaml.safe_dump(sorted([mark for mark in resp["outright_marks"]
                                     if mark["mark"] != 0],
                                    key = lambda x: -x["mark"]),
                             default_flow_style = False))
    except RuntimeError as error:
        print(f"Error: {error}")
