from model.solver import Event, RatingsSolver, HomeAdvantageRange

import json
import unittest

class SolverTest(unittest.TestCase):

    def setUp(self):
        with open("fixtures/ENG1.json") as f:
            self.events = json.loads(f.read())
    
    def filter_events(self, team_names):
        events = []
        for event in self.events:
            home_team_name, away_team_name = event["name"].split(" vs ")
            if (home_team_name in team_names and
                away_team_name in team_names):
                events.append(event)
        return events

    def test_event(self):
        event = Event({"name": "A vs B",
                       "match_odds": {"prices": [2, 3.333333333333, 5]}})
        self.assertAlmostEqual(sum(event.match_odds), 1)
        self.assertAlmostEqual(event.expected_home_points, 1.8)
        self.assertAlmostEqual(event.expected_away_points, 0.9)
    
    def test_ratings(self, home_advantage = 1.25):
        event = {"name": "A vs B",
                 "match_odds": {"prices": [2, 3, 5]}}
        team_names = ["A", "B"]    
        solver_resp = RatingsSolver().solve(events = [event],
                                            team_names = team_names,
                                            home_advantage = home_advantage,
                                            max_iterations = 1000)
        self.assertTrue(solver_resp["error"] < 0.1)
        self.assertEqual(solver_resp["home_advantage"], home_advantage)

    def test_ratings_and_bias(self,
                              team_names = ["Man City",
                                            "Liverpool",
                                            "Arsenal"]):
        events = self.filter_events(team_names)
        solver_resp = RatingsSolver().solve(events = events,
                                            team_names = team_names,
                                            max_iterations = 1000)
        self.assertTrue(solver_resp["error"] < 0.1)
        initial_bias = sum(HomeAdvantageRange) / 2
        self.assertTrue(abs(solver_resp["home_advantage"] - initial_bias) > 0.01)
                            
if __name__ == "__main__":
    unittest.main()
