import numpy as np

# Correct score matrix where rows are home goals and columns are away goals.
correct_score_matrix = np.array([
    [0.10, 0.05, 0.02],
    [0.15, 0.10, 0.05],
    [0.20, 0.15, 0.08]
])

# Compute the home win probability
def home_win_probability(matrix):
    n = matrix.shape[0]
    home_win_prob = np.sum([matrix[i, j] for i in range(n) for j in range(n) if i > j])
    return home_win_prob

# Compute the draw probability
def draw_probability(matrix):
    n = matrix.shape[0]
    draw_prob = np.sum([matrix[i, i] for i in range(n)])
    return draw_prob

# Compute the price for 0 handicap (without margin)
def price_zero_handicap(matrix):
    home_win_prob = home_win_probability(matrix)
    draw_prob = draw_probability(matrix)
    
    # Adjusted price for 0 handicap reflects the protection from a draw (push)
    effective_prob = home_win_prob / (home_win_prob + draw_prob)
    
    if effective_prob == 0:
        return float('inf')  # If no chance of a home win, price is infinite
    
    return 1 / effective_prob

# Compute the price for -0.5 handicap (without margin)
def price_minus_half_handicap(matrix):
    home_win_prob = home_win_probability(matrix)
    
    if home_win_prob == 0:
        return float('inf')  # If no chance of a home win, price is infinite
    
    return 1 / home_win_prob

# Compute the price for +0.5 handicap (without margin)
def price_plus_half_handicap(matrix):
    home_win_prob = home_win_probability(matrix)
    draw_prob = draw_probability(matrix)
    
    # For +0.5 handicap, the bet wins if home team wins or draws
    effective_prob = home_win_prob + draw_prob
    
    if effective_prob == 0:
        return float('inf')  # If no chance of a home win or draw, price is infinite
    
    return 1 / effective_prob

# Example usage:
home_win_prob = home_win_probability(correct_score_matrix)
draw_prob = draw_probability(correct_score_matrix)
price_0_handicap = price_zero_handicap(correct_score_matrix)
price_minus_half_handicap = price_minus_half_handicap(correct_score_matrix)
price_plus_half_handicap = price_plus_half_handicap(correct_score_matrix)

print(f"Home win probability: {home_win_prob}")
print(f"Draw probability: {draw_prob}")
print(f"Price for -0.5 handicap: {price_minus_half_handicap}")
print(f"Price for 0 handicap: {price_0_handicap}")
print(f"Price for +0.5 handicap: {price_plus_half_handicap}")
