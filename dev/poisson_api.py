from poisson_common import ScoreMatrix
from poisson_solver import RatingsSolver, Event
from poisson_simulator import SimPoints

from poisson_helpers import fetch_leagues, filter_team_names, calc_league_table, filter_remaining_fixtures

import fd_scraper as fd
    
if __name__=="__main__":
    try:
        import re, sys
        if len(sys.argv) < 5:
            raise RuntimeError("please enter league, cutoff, n_events, n_paths")
        leaguename, cutoff, n_events, n_paths = sys.argv[1:5]
        if not re.search("^\\D{3}\\d$", leaguename):
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
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        print ("fetching events")
        events = [Event(event)
                  for event in fd.fetch_events(leagues[leaguename])
                  if event["date"] <= cutoff]
        if events == []:
            raise RuntimeError("no events found")
        print ("%i events" % len(events))        
        team_names = filter_team_names(events)
        print ("%i teams" % len(team_names))
        results = events
        print ("%s results" % len(results))
        league_table = sorted(calc_league_table(team_names, results),
                              key = lambda x: x["name"])                        
        print ("%i table items" % len(league_table))
        remaining_fixtures = filter_remaining_fixtures(team_names, results)
        print ("%i remaining fixtures" % len(remaining_fixtures))
        training_set = sorted(events,
                             key = lambda e: e["date"])[-n_events:]
        print ("%s training set events [%s -> %s]" % (len(training_set),
                                                   training_set[0]["date"],
                                                   training_set[-1]["date"]))
        print ("solving ratings")
        solver_resp = RatingsSolver().solve(team_names=team_names,
                                            matches=training_set)
        ratings = solver_resp["ratings"]
        # print ("ratings: %s" % ratings)
        home_advantage = solver_resp["home_advantage"]
        print ("home_advantage: %.5f" % home_advantage)
        error = solver_resp["error"]
        print ("error: %.5f" % error)
        print ("simulating points")
        sim_points = SimPoints(league_table, n_paths)
        for fixture in remaining_fixtures:            
            matrix = ScoreMatrix.initialise(fixture, ratings,
                                            home_advantage = home_advantage)
            scores = matrix.simulate_points(n_paths)
            sim_points.update_event(fixture["name"], scores)
        print (sim_points.position_probabilities)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
