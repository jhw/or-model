from model.main import simulate

import json

def filter_team_names(events):
    team_names = set()
    for event in events:
        for team_name in event["name"].split(" vs "):
            team_names.add(team_name)
    return sorted(list(team_names))

if __name__ == "__main__":
    events = json.loads(open("fixtures/ENG1.json").read())
    team_names = filter_team_names(events)
    results = [event for event in events
               if event["date"] < "2024-01-01"]
    training_set = sorted(results,
                          key = lambda x: x["date"])[-60:]
    markets = [{"name": "Winner",
                "payoff": "1|19x0"}]
    print (simulate(team_names = team_names,
                    training_set = training_set,
                    results = results,
                    markets = markets,
                    n_paths = 1000))
