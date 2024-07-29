import numpy as np

import unittest

class ModelTest(unittest.TestCase):

    def test_event(self):
        from outrights.solver import Event
        event = Event({"name": "A vs B",
                       "match_odds": {"prices": [2.5, 2.5, 2.5]}})
        self.assertAlmostEqual(sum(event.training_inputs), 1)
    
    def test_score_matrix_dimensionality(self):
        from outrights.kernel import ScoreMatrix
        matrix = ScoreMatrix.initialise(event_name = "A vs B",
                                        ratings = {"A": 1,
                                                   "B": 1},
                                        home_advantage = 1.2)
        self.assertTrue(abs(np.sum(matrix.matrix) - 1) < 0.01)
        self.assertTrue(np.sum(np.tril(matrix.matrix)) > np.sum(np.triu(matrix.matrix)))

    def test_score_matrix_simulation(self, n_paths = 10000, n = 5):
        from outrights.kernel import ScoreMatrix
        matrix = ScoreMatrix.initialise(event_name = "A vs B",
                                        ratings = {"A": 1,
                                                   "B": 1},
                                        home_advantage = 1.2)
        scores = matrix.simulate_points(n_paths)
        for i in range(n):
            for j in range(n):
                target = (i, j)
                sim_prob = len([score for score in scores
                                if score == target]) / n_paths
                self.assertTrue(abs(sim_prob - matrix.matrix[i][j]) < 0.01)

    def test_points_simulation(self):
        from outrights.simulator import SimPoints
        sim_points = SimPoints(league_table = [{"name": name,
                                                "points": 0,
                                                "played": 0,
                                                "goal_difference": 0}
                                               for name in ["A", "B"]],
                               n_paths = 1000)
        sim_points.simulate(event_name = "A vs B",
                            ratings = {"A": 1,
                                       "B": 1},
                            home_advantage = 1.2)
        position_probs = sim_points.position_probabilities
        for team_name in ["A", "B"]:
            self.assertAlmostEqual(sum(position_probs[team_name]), 1)
                
    def test_league_table(self):
        from outrights.api import calc_league_table
        team_names = ["A", "B", "C"]        
        results = [{"name": "A vs B",
                    "score": (1, 0)},
                   {"name": "B vs C",
                    "score": (2, 2)},
                   {"name": "A vs C",
                    "score": (1, 2)}]
        table = {team["name"]: team for team in calc_league_table(team_names, results)}
        for team_name, points, goal_difference, played in [("A", 3, 0, 2),
                                                           ("B", 1, -1, 2),
                                                           ("C", 4, 1, 2)]:
            self.assertEqual(table[team_name]["points"], points)
            self.assertEqual(table[team_name]["goal_difference"], goal_difference)
            self.assertEqual(table[team_name]["played"], played)

    def test_remaining_fixtures(self):
        from outrights.api import calc_remaining_fixtures
        team_names = ["A", "B", "C"]        
        results = [{"name": "A vs B",
                    "score": (1, 0)},
                   {"name": "B vs C",
                    "score": (2, 2)}]
        remaining_fixtures = calc_remaining_fixtures(team_names, results)
        event_names = ['A vs C', 'B vs A', 'C vs A', 'C vs B']
        for event_name in event_names:
            self.assertTrue(event_name in remaining_fixtures)
        self.assertEqual(len(event_names), len(remaining_fixtures))
                
if __name__ == "__main__":
    unittest.main()
