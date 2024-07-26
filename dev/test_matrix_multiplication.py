import numpy as np

if __name__ == "__main__":
    home_probs = np.array([0.2, 0.8], 'd')[:, np.newaxis]
    print (home_probs)
    away_probs = np.array([0.6, 0.4], 'd')[np.newaxis, :]
    print (away_probs)
    print (home_probs * away_probs)



