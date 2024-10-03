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
    
    def probability(self, mask_fn):
        i, j = np.indices(self.matrix.shape)
        mask = mask_fn(i, j)
        return float(np.sum(self.matrix[mask]))

    def normalise(fn):
        def wrapped(self, *args, **kwargs):
            probabilities = fn(self, *args, **kwargs)
            overround = sum(probabilities)
            return [prob/overround for prob in probabilities]
        return wrapped
    
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

    def is_integer_line(self, line):
        return float(line).is_integer()

    def is_half_line(self, line):
        return (line + 0.5).is_integer()

    def is_three_quarter_line(self, line):
        return ((line > 0 and (line + 0.25).is_integer()) or
                (line < 0 and (line - 0.25).is_integer()))

    def is_quarter_line(self, line):
        return ((line > 0 and (line - 0.25).is_integer()) or
                (line < 0 and (line + 0.25).is_integer()))

    def _three_quarter_boundary_lines(self, line, offset = 0.25):
        polarity = (int(line > 0) * 2) - 1
        integer_line = line + polarity * offset
        half_line = line - polarity * offset
        return {"integer": integer_line,
                "half": half_line}    
    
    def _quarter_boundary_lines(self, line, offset = 0.25):
        polarity = (int(line > 0) * 2) - 1
        integer_line = line - polarity * offset
        half_line = line + polarity * offset
        return {"integer": integer_line,
                "half": half_line}    

    def _home_half_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) > 0)

    def _away_half_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) < 0)

    """
    def _home_integer_handicap(self, line):
        win_prob = self._home_half_handicap(line)
        draw_prob = self.probability(lambda i, j: (i + line - j) == 0)
        denominator = win_prob + draw_prob
        return 0.0 if denominator == 0 else win_prob / denominator
    
    def _away_integer_handicap(self, line):
        win_prob = self._away_half_handicap(line)
        draw_prob = self.probability(lambda i, j: (i + line - j) == 0)
        denominator = win_prob + draw_prob
        return 0.0 if denominator == 0 else win_prob / denominator
    """

    def _home_integer_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) >= 0)

    def _away_integer_handicap(self, line):
        return self.probability(lambda i, j: (i + line - j) <= 0)
    
    def _home_three_quarter_handicap(self, line):
        boundary_lines = self._three_quarter_boundary_lines(line)
        integer_prob = self._home_integer_handicap(boundary_lines["integer"])
        half_prob = self._home_half_handicap(boundary_lines["half"])
        return (integer_prob + half_prob) / 2

    def _away_three_quarter_handicap(self, line):
        boundary_lines = self._three_quarter_boundary_lines(line)
        integer_prob = self._away_integer_handicap(boundary_lines["integer"])
        half_prob = self._away_half_handicap(boundary_lines["half"])
        return (integer_prob + half_prob) / 2
    
    def _home_quarter_handicap(self, line):
        boundary_lines = self._quarter_boundary_lines(line)
        integer_prob = self._home_integer_handicap(boundary_lines["integer"])
        half_prob = self._home_half_handicap(boundary_lines["half"])
        return (integer_prob + half_prob) / 2

    def _away_quarter_handicap(self, line):
        boundary_lines = self._quarter_boundary_lines(line)
        integer_prob = self._away_integer_handicap(boundary_lines["integer"])
        half_prob = self._away_half_handicap(boundary_lines["half"])
        return (integer_prob + half_prob) / 2
            
    def _home_handicap(self, line):
        if self.is_integer_line(line):
            return self._home_integer_handicap(line)
        elif self.is_half_line(line):
            return self._home_half_handicap(line)
        elif self.is_three_quarter_line(line):
            return self._home_three_quarter_handicap(line)
        elif self.is_quarter_line(line):
            return self._home_quarter_handicap(line)
        else:
            raise RuntimeError(f"couldn't match AH home line for {line}")

    def _away_handicap(self, line):
        if self.is_integer_line(line):
            return self._away_integer_handicap(line)
        elif self.is_half_line(line):
            return self._away_half_handicap(line)
        elif self.is_three_quarter_line(line):
            return self._away_three_quarter_handicap(line)
        elif self.is_quarter_line(line):          
            return self._away_quarter_handicap(line)
        else:
            raise RuntimeError(f"couldn't match AH away line for {line}")

    def _asian_handicaps(self, line):
        return [self._home_handicap(line),
                self._away_handicap(line)]

    @normalise
    def asian_handicaps(self, line):
        return self._asian_handicaps(line)

    @property
    def asian_handicap_lines(self, interval = 0.25):
        n = int(self.n / interval)
        lines = [i * interval for i in range(-n + 1, n)]
        return [(line, self.asian_handicaps(line))
                for line in lines]
    
    ### over/under goals

    def _over_goals(self, line):
        return self.probability(lambda i, j: (i + j) > line)

    def _under_goals(self, line):
        return self.probability(lambda i, j: (i + j) < line)

    def _over_under_goals(self, line):
        return [self._over_goals(line),
                self._under_goals(line)]

    @normalise
    def over_under_goals(self, line):
        return self._over_under_goals(line)

    @property
    def over_under_goals_lines(self, interval = 0.25):
        lines = [i + 0.5 for i in range(self.n)]
        return [(line, self.over_under_goals(line))
                for line in lines]
    
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
