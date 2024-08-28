from model.markets import init_markets

import unittest

class MarketsTest(unittest.TestCase):

    def test_initialisation(self):
        try:
            init_markets(team_names = ["A", "B", "C"],
                         markets = [{"name": "Standard",
                                     "payoff": "1|2x0"},
                                    {"name": "Include",
                                     "payoff": "1|0",
                                     "include": ["A", "B"]},
                                    {"name": "Exclude",
                                     "payoff": "1|0",
                                     "exclude": "A"}])
        except Exception as error:
            self.fail(str(error))
            
if __name__ == "__main__":
    unittest.main()
