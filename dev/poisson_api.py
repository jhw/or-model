from poisson_common import ScoreMatrix
from poisson_solver import RatingsSolver, Event
from poisson_simulator import SimPoints

from poisson_helpers import fetch_leagues, calc_league_table, calc_remaining_fixtures

import fd_scraper as fd

def calc_ppg_ratings(team_names, ratings, home_advantage):
    ppg_ratings = {team_name: 0 for team_name in team_names}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:
                event_name = f"{home_team_name} vs {away_team_name}"
                matrix = ScoreMatrix.initialise(event_name = event_name,
                                                ratings = ratings,
                                                home_advantage = home_advantage)
                home_win_prob, draw_prob, away_win_prob = matrix.match_odds
                ppg_ratings[home_team_name] += 3 * home_win_prob + draw_prob
                ppg_ratings[away_team_name] += 3 * away_win_prob + draw_prob
    n_games = (len(team_names) - 1) * 2
    return {team_name:ppg_value / n_games
            for team_name, ppg_value in ppg_ratings.items()}

def simulate(team_names, training_set, results, rounds):
    league_table = sorted(calc_league_table(team_names = team_names,
                                            results = results),
                          key = lambda x: x["name"])                        
    remaining_fixtures = calc_remaining_fixtures(team_names = team_names,
                                                 results = results,
                                                 rounds = rounds)
    solver_resp = RatingsSolver().solve(team_names = team_names,
                                        matches = training_set)
    poisson_ratings = solver_resp["ratings"]
    home_advantage = solver_resp["home_advantage"]
    solver_error = solver_resp["error"]
    sim_points = SimPoints(league_table, n_paths)
    for event_name in remaining_fixtures:
        sim_points.simulate(event_name = event_name,
                            ratings = poisson_ratings,
                            home_advantage = home_advantage,
                            n_paths = n_paths)
    position_probabilities = sim_points.position_probabilities
    ppg_ratings = calc_ppg_ratings(team_names = team_names,
                                   ratings = poisson_ratings,
                                   home_advantage = home_advantage)
    teams = [{"name": team_name,
              "poisson_rating": poisson_ratings[team_name],
              "ppg_rating": ppg_ratings[team_name],
              "position_probabilities": position_probabilities[team_name]}
             for team_name in team_names]
    return {"teams": teams,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

"""
not fetching from or-teams as using historical data
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
        events = [Event(event)
                  for event in fd.fetch_events(leagues[league_name])
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
        sim_resp = simulate(team_names = team_names,
                            results = results,
                            training_set = training_set,
                            rounds = rounds)
        import json
        print ()
        print (json.dumps(sim_resp,
                          indent = 2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
