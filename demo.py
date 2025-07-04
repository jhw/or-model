from model.solver import RatingRange
from model.main import simulate

import json
import logging
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


if __name__ == "__main__":
    # Configure logging to show solver iterations
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        league_name = sys.argv[1]
        if not re.search("^\\D{3}\\d{1}", league_name):
            raise RuntimeError("league is invalid")
        file_name = f"fixtures/{league_name}.json"
        if not os.path.exists(file_name):
            raise RuntimeError(f"{file_name} does not exist")
        events = json.loads(open(file_name).read())
        team_names = filter_team_names(events)
        ratings = {team_name: random.uniform(*RatingRange)
                   for team_name in team_names}
        training_set = sorted(events,
                              key = lambda x: x["date"])[-3*len(team_names):]
        winner_payoff = f"1|{len(team_names)-1}x0"
        markets = [{"name": "Winner",
                    "payoff": winner_payoff}]
        rounds = 2 if "SCO" in league_name else 1
        resp = simulate(ratings = ratings,
                        training_set = training_set,
                        events = events,
                        handicaps = {},
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
