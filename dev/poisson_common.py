from scipy.special import factorial
import numpy as np

# Poisson Probability Function
def poisson_prob(lmbda, k):
    return (lmbda ** k) * np.exp(-lmbda) / factorial(k)

# Dixon-Coles Adjustment Function
def dixon_coles_adjustment(i, j, rho):
    if i == 0 and j == 0:
        return 1 - (i * j * rho)
    elif i == 0 and j == 1:
        return 1 + (rho / 2)
    elif i == 1 and j == 0:
        return 1 + (rho / 2)
    elif i == 1 and j == 1:
        return 1 - rho
    else:
        return 1

# ScoreMatrix Class
class ScoreMatrix:
    @classmethod
    def initialise(self, match, ratings, rho=0.1, home_advantage=1.2):
        hometeamname, awayteamname = match["name"].split(" vs ")
        home_lambda = ratings[hometeamname] * home_advantage
        away_lambda = ratings[awayteamname]
        return ScoreMatrix(home_lambda, away_lambda, rho)
    
    def __init__(self, home_lambda, away_lambda, rho=0.1):
        self.home_lambda = home_lambda
        self.away_lambda = away_lambda
        self.rho = rho
        self.matrix = self.init_matrix()

    def init_matrix(self, n=11):
        home_goals = np.arange(n)
        away_goals = np.arange(n)
        home_probs = poisson_prob(self.home_lambda, home_goals[:, np.newaxis])
        away_probs = poisson_prob(self.away_lambda, away_goals[np.newaxis, :])
        dixon_coles_matrix = np.vectorize(dixon_coles_adjustment)(home_goals[:, np.newaxis], away_goals[np.newaxis, :], self.rho)
        return home_probs * away_probs * dixon_coles_matrix

    @property
    def home_win(self, home_handicap_offset = 0):
        return np.sum(np.tril(self.matrix, -1 + home_handicap_offset))

    @property
    def draw(self):
        return np.sum(np.diag(self.matrix))

    @property
    def away_win(self, home_handicap_offset = 0):
        return np.sum(np.triu(self.matrix, 1 + home_handicap_offset))

    def normalise(fn):
        def wrapped(self):
            probabilities = fn(self)
            overround = sum(probabilities)
            return [prob/overround for prob in probabilities]
        return wrapped

    @property
    @normalise
    def match_odds(self):
        return [self.home_win, self.draw, self.away_win]

    @property
    def training_inputs(self):
        return self.match_odds

# Event Class
class Event(dict):
    def __init__(self, event):
        dict.__init__(self, event)

    def probabilities(self, attr):
        probs = [1 / price for price in self[attr]["prices"]]
        overround = sum(probs)
        return [prob / overround for prob in probs]

    @property
    def match_odds(self):
        return self.probabilities("match_odds")

    @property
    def training_inputs(self):
        return self.match_odds

if __name__ == "__main__":
    pass
