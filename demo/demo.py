from outrights.api import simulate
import fd_scraper as fd
import json, urllib.request

def fetch_leagues():
    return json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())

"""
not fetching from teams.outrights.net as generally using historical data here
"""

def filter_team_names(events):
    team_names = set()
    for event in events:
        for team_name in event["name"].split(" vs "):
            team_names.add(team_name)
    return sorted(list(team_names))

if __name__=="__main__":
    try:
        import re, sys
        if len(sys.argv) < 5:
            raise RuntimeError("please enter league, cutoff, n_events, n_paths")
        league_name, cutoff, n_events, n_paths = sys.argv[1:5]
        if not re.search("^\\D{3}\\d$", league_name):
            raise RuntimeError("league is invalid")
        if not re.search("^\\d{4}\\-\\d{2}\\-\\d{2}$", cutoff):
            raise RuntimeError("cutoff is invalid")
        if not re.search("^\\d+$", n_events):
            raise RuntimeError("n_events is invalid")
        n_events = int(n_events)
        if not re.search("^\\d+$", n_paths):
            raise RuntimeError("n_paths is invalid")
        n_paths = int(n_paths)
        print ("fetching leagues")
        leagues={league["name"]: league
                 for league in fetch_leagues()}
        if league_name not in leagues:
            raise RuntimeError("league not found")
        print ("fetching events")
        events = [event for event in fd.fetch_events(leagues[league_name])
                  if event["date"] <= cutoff]
        if events == []:
            raise RuntimeError("no events found")
        team_names = filter_team_names(events)
        print ("%i teams" % len(team_names))
        results = events
        print ("%s results" % len(results))
        training_set = sorted(events,
                              key = lambda e: e["date"])[-n_events:]
        print ("%s TS events [%s -> %s]" % (len(training_set),
                                            training_set[0]["date"],
                                            training_set[-1]["date"]))
        print ("simulating")
        rounds = 2 if league_name.startswith("SCO") else 1
        resp = simulate(team_names = team_names,
                        results = results,
                        training_set = training_set,
                        rounds = rounds,
                        n_paths = n_paths)
        print ("home_advantage: %.5f" % resp["home_advantage"])
        print ("solver_error: %.5f" % resp["solver_error"])
        with open("tmp/%s.json" % league_name, 'w') as f:
            f.write(json.dumps(resp,
                               indent = 2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
