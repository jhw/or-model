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
 
    def test_asian_handicaps(self, lines = [0.25 * (i - 10) for i in range(21)]):
        self.assertTrue(self.matrix._home_handicap(0.25) > self.matrix._home_handicap(-0.25))
        self.assertTrue(self.matrix._away_handicap(0.25) < self.matrix._away_handicap(-0.25))
        line_prices = [self.matrix._asian_handicaps(line) for line in lines]
        for line, prices in zip(lines, line_prices):
            # self.assertTrue(abs(sum(prices) - 1) < 0.01)
            pass
        home_prices = [prices[0] for prices in line_prices]
        self.assertEqual(home_prices, sorted(home_prices))
        away_prices = [prices[1] for prices in line_prices]
        self.assertEqual(away_prices, list(reversed(sorted(away_prices))))

    def test_over_under_goals(self, lines = [i + 0.5 for i in range(10)]):
        self.assertTrue(self.matrix._over_goals(0.5) > self.matrix._over_goals(1.5))
        self.assertTrue(self.matrix._under_goals(0.5) < self.matrix._under_goals(1.5))
        line_prices = [self.matrix._over_under_goals(line) for line in lines]
        for prices in line_prices:
            self.assertTrue(abs(sum(prices) - 1) < 0.01)
        over_prices = [prices[0] for prices in line_prices]
        self.assertEqual(over_prices, list(reversed(sorted(over_prices))))
        under_prices = [prices[1] for prices in line_prices]
        self.assertEqual(under_prices, sorted(under_prices))

    def test_normalisation(self):
        self.assertAlmostEqual(sum(self.matrix.match_odds), 1)
        self.assertAlmostEqual(sum(self.matrix.asian_handicaps(-0.5)), 1)
        self.assertAlmostEqual(sum(self.matrix.over_under_goals(2.5)), 1)

if __name__ == "__main__":
    unittest.main()
