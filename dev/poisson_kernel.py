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
    def initialise(self, event_name, ratings, home_advantage, rho=0.1):
        home_team_name, away_team_name = event_name.split(" vs ")
        home_lambda = ratings[home_team_name] * home_advantage
        away_lambda = ratings[away_team_name]
        return ScoreMatrix(home_lambda, away_lambda, rho)
    
    def __init__(self, home_lambda, away_lambda, rho):
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

    def simulate_points(self, n_paths):
        flat_matrix = self.matrix.flatten() 
        chosen_indices = np.random.choice(len(flat_matrix),
                                          size=n_paths,
                                          p=flat_matrix / flat_matrix.sum())
        indexes = [(i, j)
                   for i in range(self.matrix.shape[0])
                   for j in range(self.matrix.shape[1])]
        return [indexes[i] for i in chosen_indices]

if __name__ == "__main__":
    pass
