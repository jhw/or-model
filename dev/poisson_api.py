from poisson_common import ScoreMatrix
from poisson_solver import RatingsSolver, Event
from poisson_simulator import SimPoints

from poisson_helpers import fetch_leagues, filter_team_names, calc_league_table, calc_remaining_fixtures

import fd_scraper as fd

"""
- no point including rounds here
"""

def calc_points_per_game(team_names, ratings, home_advantage):
    points_per_game = {team_name: 0 for team_name in team_names}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:
                event_name = f"{home_team_name} vs {away_team_name}"
                match = {"name": event_name}
                matrix = ScoreMatrix.initialise(match = match,
                                                ratings = ratings,
                                                home_advantage = home_advantage)
                home_win_prob, draw_prob, away_win_prob = matrix.match_odds
                points_per_game[home_team_name] += 3 * home_win_prob + draw_prob
                points_per_game[away_team_name] += 3 * away_win_prob + draw_prob
    n_games = (len(team_names) - 1) * 2
    return {team_name:ppg_value / n_games
            for team_name, ppg_value in points_per_game.items()}

def simulate(team_names, training_set, results):
    league_table = sorted(calc_league_table(team_names, results),
                          key = lambda x: x["name"])                        
    remaining_fixtures = calc_remaining_fixtures(team_names, results)
    solver_resp = RatingsSolver().solve(team_names=team_names,
                                        matches=training_set)
    ratings = solver_resp["ratings"]
    home_advantage = solver_resp["home_advantage"]
    solver_error = solver_resp["error"]
    sim_points = SimPoints(league_table, n_paths)
    for fixture in remaining_fixtures:
        sim_points.simulate(fixture = fixture,
                            ratings = ratings,
                            home_advantage = home_advantage,
                            n_paths = n_paths)
    position_probabilities = sim_points.position_probabilities
    points_per_game = calc_points_per_game(team_names = team_names,
                                           ratings = ratings,
                                           home_advantage = home_advantage)
    teams = [{"name": team_name,
              "poisson_rating": ratings[team_name],
              "position_probabilities": position_probabilities[team_name],
              "expected_points_per_game": points_per_game[team_name]}
             for team_name in team_names]
    return {"teams": teams,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

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
        sim_resp = simulate(team_names = team_names,
                            results = results,
                            training_set = training_set)
        import json
        print ()
        print (json.dumps(sim_resp,
                          indent = 2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
