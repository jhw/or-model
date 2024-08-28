from model.simulator import SimPoints
import numpy as np

import unittest

class SimTest(unittest.TestCase):
                
    def test_position_probabilities(self):
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
        for team_names in [["A", "B"],
                           ["A"]]: # test mask
            position_probs = sim_points.position_probabilities(team_names = team_names)
            self.assertEqual(len(team_names), len(position_probs))
            for team_name in team_names:
                self.assertAlmostEqual(sum(position_probs[team_name]), 1)
                            
if __name__ == "__main__":
    unittest.main()
