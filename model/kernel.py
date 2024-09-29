from scipy.special import factorial

import math
import numpy as np

def poisson_prob(lmbda, k):
    return (lmbda ** k) * np.exp(-lmbda) / factorial(k)

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

def linear_interpolate(xy_coords, x):
    if x < xy_coords[0][0] or x > xy_coords[-1][0]:
        raise RuntimeError("the x value is out of the interpolation range")
    for i in range(len(xy_coords) - 1):
        x0, y0 = xy_coords[i]
        x1, y1 = xy_coords[i + 1]        
        if x0 <= x <= x1:
            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            return y
    raise RuntimeError("interpolation failed due to unexpected input")
    
class ScoreMatrix:

    @classmethod
    def initialise(self, event_name, ratings, home_advantage, n = 11, rho = 0.1):
        home_team_name, away_team_name = event_name.split(" vs ")
        home_lambda = ratings[home_team_name] * home_advantage
        away_lambda = ratings[away_team_name]
        return ScoreMatrix(home_lambda, away_lambda, n, rho)
    
    def __init__(self, home_lambda, away_lambda, n, rho):
        self.home_lambda = home_lambda
        self.away_lambda = away_lambda
        self.rho = rho
        self.matrix = self.init_matrix(n)

    def init_matrix(self, n):
        home_goals = np.arange(n)
        away_goals = np.arange(n)
        home_probs = poisson_prob(self.home_lambda, home_goals[:, np.newaxis])
        away_probs = poisson_prob(self.away_lambda, away_goals[np.newaxis, :])
        dixon_coles_matrix = np.vectorize(dixon_coles_adjustment)(home_goals[:, np.newaxis], away_goals[np.newaxis, :], self.rho)
        return home_probs * away_probs * dixon_coles_matrix

    @property
    def n(self):
        return len(self.matrix)
    
    def simulate_scores(self, n_paths):
        flat_matrix = self.matrix.flatten() 
        chosen_indices = np.random.choice(len(flat_matrix),
                                          size=n_paths,
                                          p=flat_matrix / flat_matrix.sum())
        indexes = [(i, j)
                   for i in range(self.matrix.shape[0])
                   for j in range(self.matrix.shape[1])]
        return [indexes[i] for i in chosen_indices]
    
    def enforce_half_line(fn):
        def wrapped(self, line):
            if not (line - 0.5).is_integer():
                raise RuntimeError(f"line must be a half line: {line}")
            return fn(self, line)
        return wrapped
    
    def normalise(fn):
        def wrapped(self, *args, **kwargs):
            probabilities = fn(self, *args, **kwargs)
            overround = sum(probabilities)
            return [prob/overround for prob in probabilities]
        return wrapped

    def probability(self, mask_fn):
        i, j = np.indices(self.matrix.shape)
        mask = mask_fn(i, j)
        return float(np.sum(self.matrix[mask]))
    
    ### match odds
    
    @property
    def _home_win(self):
        return self.probability(lambda i, j: i > j)

    @property
    def _draw(self):
        return self.probability(lambda i, j: i == j)

    @property
    def _away_win(self):
        return self.probability(lambda i, j: i < j)

    @property
    def _match_odds(self):
        return [self._home_win, self._draw, self._away_win]

    @property
    @normalise
    def match_odds(self):
        return self._match_odds
    
    ### asian handicap

    @enforce_half_line
    def __home_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) > 0)

    @enforce_half_line
    def __away_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) < 0)

    def handle_handicap_half_line(fn):
        def wrapped(self, handicap_fn, line):            
            return handicap_fn(line) if (line - 0.5).is_integer() else fn(self, handicap_fn, line)
        return wrapped
    
    @handle_handicap_half_line
    def _interpolate_handicap(self, handicap_fn, line):
        lower_line = round(line) - 0.5
        upper_line = lower_line + 1
        lower_prob = handicap_fn(lower_line)
        upper_prob = handicap_fn(upper_line)
        return linear_interpolate([(lower_line, lower_prob),
                                   (upper_line, upper_prob)], line)
    
    def _home_handicap(self, line):
        return self._interpolate_handicap(handicap_fn = self.__home_handicap,
                                          line = line)

    def _away_handicap(self, line):
        return self._interpolate_handicap(handicap_fn = self.__away_handicap,
                                          line = line)

    def _asian_handicaps(self, line):
        return [self._home_handicap(line),
                self._away_handicap(line)]

    @normalise
    def asian_handicaps(self, line):
        return self._asian_handicaps(line)

    @property
    def _handicap_half_lines(self):
        lines = [i - math.ceil(self.n/2) + 0.5
                 for i in range(self.n + 1)]
        return [(line, self.asian_handicaps(line))
                for line in lines]

    @property
    def asian_handicap_moneyline(self):
        half_lines = self._handicap_half_lines
        xy_coords = [(prices[0], line) for line, prices in half_lines]
        return linear_interpolate(xy_coords, 0.5)
    
    ### over/under goals

    @enforce_half_line
    def _over_goals(self, line):
        return self.probability(lambda i, j: (i + j) > line)

    @enforce_half_line
    def _under_goals(self, line):
        return self.probability(lambda i, j: (i + j) < line)

    def _over_under_goals(self, line):
        return [self._over_goals(line),
                self._under_goals(line)]

    @normalise
    def over_under_goals(self, line):
        return self._over_under_goals(line)

    ### expected points
    
    @property
    def expected_home_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[0] + match_odds[1]

    @property
    def expected_away_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[2] + match_odds[1]

if __name__ == "__main__":
    pass
