from model.kernel import ScoreMatrix
import numpy as np

import unittest

class KernelTest(unittest.TestCase):
    
    def test_dimensionality(self):
        matrix = ScoreMatrix.initialise(event_name = "A vs B",
                                        ratings = {"A": 1,
                                                   "B": 1},
                                        home_advantage = 1.2)
        self.assertTrue(abs(np.sum(matrix.matrix) - 1) < 0.01)
        self.assertTrue(np.sum(np.tril(matrix.matrix)) > np.sum(np.triu(matrix.matrix)))

    def test_simulation(self, n_paths = 10000, n = 5):
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
            
if __name__ == "__main__":
    unittest.main()
