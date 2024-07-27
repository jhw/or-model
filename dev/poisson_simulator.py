from poisson_common import ScoreMatrix
from poisson_solver import RatingsSolver, Event
from poisson_helpers import fetch_leagues, filter_team_names, calc_league_table, filter_remaining_fixtures

import numpy as np

import fd_scraper as fd

class SimPoints:

    GDMultiplier = 1e-4
    
    def __init__(self, league_table, n_paths):
        self.n_paths = n_paths
        self.team_names = [team["name"] for team in league_table]
        self.points = self._init_points_array(league_table)

    def _init_points_array(self, league_table):
        points_array = np.zeros((len(league_table), self.n_paths))
        for i, team in enumerate(league_table):
            points_with_goal_diff = team['points'] + self.GDMultiplier * team['goal_difference']
            points_array[i, :] = points_with_goal_diff
        return points_array

    def get_team_points(self, team_name):
        team_index = self.team_names.index(team_name)
        return self.points[team_index]

    def update_home_team(self, team_name, scores):
        points = np.array([3*int(score[0] > score[1]) + int(score[0] == score[1])
                           for score in scores])
        goal_difference = np.array([score[0]-score[1] for score in scores])
        team_index = self.team_names.index(team_name)
        self.points[team_index] += points + self.GDMultiplier * goal_difference

    def update_away_team(self, team_name, scores):
        points = np.array([3*int(score[1] > score[0]) + int(score[0] == score[1])
                           for score in scores])
        goal_difference = np.array([score[1]-score[0] for score in scores])
        team_index = self.team_names.index(team_name)
        self.points[team_index] += points + self.GDMultiplier * goal_difference

    def update_event(self, event_name, scores):
        home_team_name, away_team_name = event_name.split(" vs ")
        self.update_home_team(home_team_name, scores)
        self.update_away_team(away_team_name, scores)

    @property
    def positions(self):
        return len(self.points) - np.argsort(np.argsort(self.points, axis=0), axis=0) - 1

    @property
    def position_probabilities(self):
        counts = np.zeros((len(self.points), len(self.points)))
        for i, row in enumerate(self.positions):
            for j in row:
                counts[i][j] += 1
        return counts / self.n_paths
    
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
        """
        print ()
        print (sim_points.points)
        print ()
        print (sim_points.positions)
        print ()
        """
        print (sim_points.position_probabilities)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
