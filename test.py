import numpy as np

import unittest

class ModelTest(unittest.TestCase):

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
                
if __name__ == "__main__":
    unittest.main()
