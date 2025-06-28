from model.state import calc_league_table, calc_remaining_fixtures

import unittest

class StateTest(unittest.TestCase):
                
    def test_league_table(self):

        team_names = ["A", "B", "C"]        
        events = [{"name": "A vs B",
                   "score": (1, 0)},
                  {"name": "B vs C",
                   "score": (2, 2)},
                  {"name": "A vs C",
                   "score": (1, 2)}]
        table = {team["name"]: team for team in calc_league_table(team_names = team_names,
                                                                  events = events,
                                                                  handicaps = {})}
        for team_name, points, goal_difference, played in [("A", 3, 0, 2),
                                                           ("B", 1, -1, 2),
                                                           ("C", 4, 1, 2)]:
            self.assertEqual(table[team_name]["points"], points)
            self.assertEqual(table[team_name]["goal_difference"], goal_difference)
            self.assertEqual(table[team_name]["played"], played)

    def test_remaining_fixtures(self):
        from model.state import calc_remaining_fixtures
        team_names = ["A", "B", "C"]        
        events = [{"name": "A vs B",
                   "score": (1, 0)},
                  {"name": "B vs C",
                   "score": (2, 2)}]
        remaining_fixtures = calc_remaining_fixtures(team_names = team_names,
                                                     events = events)
        event_names = ['A vs C', 'B vs A', 'C vs A', 'C vs B']
        for event_name in event_names:
            self.assertTrue(event_name in remaining_fixtures)
        self.assertEqual(len(event_names), len(remaining_fixtures))
            
if __name__ == "__main__":
    unittest.main()
