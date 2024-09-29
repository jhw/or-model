from model.solver import RatingsSolver, RatingRange, HomeAdvantageRange

import json
import random
import unittest

def filter_1x2_probabilities(event):
    probs = [1 / price for price in event["match_odds"]["prices"]]
    overround = sum(probs)
    return [prob / overround for prob in probs]

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
    
    def test_ratings(self,
                     model_selector = lambda event, matrix: matrix.match_odds,
                     market_selector = lambda event: filter_1x2_probabilities(event),
                     rating_range = RatingRange,
                     home_advantage_range = HomeAdvantageRange):
        event = {"name": "A vs B",
                 "match_odds": {"prices": [2, 3, 5]}}
        ratings = {team_name: random.uniform(*rating_range)
                   for team_name in ["A", "B"]}
        home_advantage = sum(home_advantage_range) / 2
        solver = RatingsSolver(model_selector = model_selector,
                               market_selector = market_selector)
        solver_resp = solver.solve(events = [event],
                                   ratings = ratings,
                                   home_advantage = home_advantage,
                                   max_iterations = 1000)
        self.assertTrue(solver_resp["error"] < 0.1)
        self.assertEqual(solver_resp["home_advantage"], home_advantage)

    def test_ratings_and_bias(self,
                              team_names = ["Man City",
                                            "Liverpool",
                                            "Arsenal"],
                              model_selector = lambda event, matrix: matrix.match_odds,
                              market_selector = lambda event: filter_1x2_probabilities(event),
                              rating_range = RatingRange):
        events = self.filter_events(team_names)
        ratings = {team_name: random.uniform(*rating_range)
                   for team_name in team_names}
        solver = RatingsSolver(model_selector = model_selector,
                               market_selector = market_selector)
        solver_resp = solver.solve(events = events,
                                   ratings = ratings,
                                   max_iterations = 1000)
        self.assertTrue(solver_resp["error"] < 0.1)
        initial_bias = sum(HomeAdvantageRange) / 2
        self.assertTrue(abs(solver_resp["home_advantage"] - initial_bias) > 0.01)
                            
if __name__ == "__main__":
    unittest.main()
