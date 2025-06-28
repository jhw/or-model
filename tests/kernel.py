from model.kernel import ScoreMatrix
import numpy as np

import unittest

class KernelTest(unittest.TestCase):

    def setUp(self):
        self.matrix = ScoreMatrix.initialise(event_name = "A vs B",
                                             ratings = {"A": 1,
                                                        "B": 1},
                                             home_advantage = 1.2)

    def test_consistency(self):
        self.assertTrue(abs(np.sum(self.matrix.matrix) - 1) < 0.01)

    def test_dimensionality(self):
        self.assertTrue(np.sum(np.tril(self.matrix.matrix)) > np.sum(np.triu(self.matrix.matrix)))

    def test_simulate_scores(self, n_paths = 10000, n = 5):
        scores = self.matrix.simulate_scores(n_paths)
        for i in range(n):
            for j in range(n):
                target = (i, j)
                sim_prob = len([score for score in scores
                                if score == target]) / n_paths
                self.assertTrue(abs(sim_prob - self.matrix.matrix[i][j]) < 0.01)
                

    def test_match_odds(self):
        match_odds = [self.matrix._home_win,
                      self.matrix._draw,
                      self.matrix._away_win]
        self.assertTrue(abs(sum(match_odds) - 1) < 0.01)
        self.assertTrue(abs(sum(self.matrix._match_odds) - 1) < 0.01)
 

    def test_normalisation(self):
        self.assertAlmostEqual(sum(self.matrix.match_odds), 1)

            
if __name__ == "__main__":
    unittest.main()
