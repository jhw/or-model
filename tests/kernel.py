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
        for line, resp in [(0, True),
                           (1, True),
                           (0.5, False),
                           (0.25, False),
                           (0.75, False),
                           (-1, True),
                           (-0.5, False),
                           (-0.25, False),
                           (-0.75, False)]:
            self.assertEqual(self.matrix.is_integer_line(line), resp)

    def test_is_half_line(self):
        for line, resp in [(0, False),
                           (1, False),
                           (0.5, True),
                           (0.25, False),
                           (0.75, False),
                           (-1, False),
                           (-0.5, True),
                           (-0.25, False),
                           (-0.75, False)]:
            self.assertEqual(self.matrix.is_half_line(line), resp)

    def test_is_quarter_line(self):
        for line, resp in [(0, False),
                           (1, False),
                           (0.5, False),
                           (0.25, True),
                           (0.75, False),
                           (-1, False),
                           (-0.5, False),
                           (-0.25, True),
                           (-0.75, False)]:
            self.assertEqual(self.matrix.is_quarter_line(line), resp)

    def test_is_three_quarter_line(self):
        for line, resp in [(0, False),
                           (1, False),
                           (0.5, False),
                           (0.25, False),
                           (0.75, True),
                           (-1, False),
                           (-0.5, False),
                           (-0.25, False),
                           (-0.75, True)]:
            self.assertEqual(self.matrix.is_three_quarter_line(line), resp)

    def test_quarter_boundary_lines(self):
        for line, integer_line, half_line in [(0.25, 0, 0.5),
                                              (1.25, 1, 1.5),
                                              (-0.25, 0, -0.5),
                                              (-1.25, -1, -1.5)]:
            boundary_lines = self.matrix._quarter_boundary_lines(line)
            self.assertEqual(integer_line, boundary_lines["integer"])
            self.assertEqual(half_line, boundary_lines["half"])

    def test_three_quarter_boundary_lines(self):
        for line, integer_line, half_line in [(0.75, 1, 0.5),
                                              (1.75, 2, 1.5),
                                              (-0.75, -1, -0.5),
                                              (-1.75, -2, -1.5)]:
            boundary_lines = self.matrix._three_quarter_boundary_lines(line)
            self.assertEqual(integer_line, boundary_lines["integer"])
            self.assertEqual(half_line, boundary_lines["half"])

    def test_match_odds(self):
        match_odds = [self.matrix._home_win,
                      self.matrix._draw,
                      self.matrix._away_win]
        self.assertTrue(abs(sum(match_odds) - 1) < 0.01)
        self.assertTrue(abs(sum(self.matrix._match_odds) - 1) < 0.01)
 
    def test_asian_handicaps(self):
        self.assertTrue(self.matrix._home_handicap(0.5) > self.matrix._home_handicap(-0.5))
        self.assertTrue(self.matrix._away_handicap(0.5) < self.matrix._away_handicap(-0.5))
        home_prices = [item[1][0] for item in self.matrix.asian_handicap_lines]
        self.assertEqual(home_prices, sorted(home_prices))

    def test_over_under_goals(self):
        self.assertTrue(self.matrix._over_goals(0.5) > self.matrix._over_goals(1.5))
        self.assertTrue(self.matrix._under_goals(0.5) < self.matrix._under_goals(1.5))
        under_prices = [item[1][1] for item in self.matrix.over_under_goals_lines]
        self.assertEqual(under_prices, sorted(under_prices))

    def test_normalisation(self):
        self.assertAlmostEqual(sum(self.matrix.match_odds), 1)
        self.assertAlmostEqual(sum(self.matrix.asian_handicaps(-0.5)), 1)
        self.assertAlmostEqual(sum(self.matrix.over_under_goals(2.5)), 1)

            
if __name__ == "__main__":
    unittest.main()
