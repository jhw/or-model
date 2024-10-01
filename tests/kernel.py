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
                
    def test_is_integer_line(self):
        for num, resp in [(0, True),
                          (1, True),
                          (0.5, False),
                          (0.25, False),
                          (0.75, False),
                          (-1, True),
                          (-0.5, False),
                          (-0.25, False),
                          (-0.75, False)]:
            self.assertEqual(self.matrix.is_integer_line(num), resp)

    def test_is_half_line(self):
        for num, resp in [(0, False),
                          (1, False),
                          (0.5, True),
                          (0.25, False),
                          (0.75, False),
                          (-1, False),
                          (-0.5, True),
                          (-0.25, False),
                          (-0.75, False)]:
            self.assertEqual(self.matrix.is_half_line(num), resp)

    def test_is_quarter_line(self):
        for num, resp in [(0, False),
                          (1, False),
                          (0.5, False),
                          (0.25, True),
                          (0.75, False),
                          (-1, False),
                          (-0.5, False),
                          (-0.25, True),
                          (-0.75, False)]:
            self.assertEqual(self.matrix.is_quarter_line(num), resp)

    def test_is_three_quarter_line(self):
        for num, resp in [(0, False),
                          (1, False),
                          (0.5, False),
                          (0.25, False),
                          (0.75, True),
                          (-1, False),
                          (-0.5, False),
                          (-0.25, False),
                          (-0.75, True)]:
            self.assertEqual(self.matrix.is_three_quarter_line(num), resp)
            
if __name__ == "__main__":
    unittest.main()
