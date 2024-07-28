import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import json
import os
import sys

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league name")
        league_name = sys.argv[1]
        if not os.path.exists(f"tmp/{league_name}.json"):
            raise RuntimeError("data file does not exist")        
        with open(f"tmp/{league_name}.json", 'r') as file:
            data = json.load(file)
        teams = [team['name'] for team in data['teams']]
        position_probabilities = [team['position_probabilities']
                                  for team in data['teams']]
        position_probabilities = np.array(position_probabilities)
        plt.figure(figsize=(12, 12))
        sns.heatmap(position_probabilities,
                    cmap='Reds',
                    yticklabels=teams,
                    xticklabels=np.arange(1, len(teams)+1))
        plt.title(f"{league_name} Position Probability Heatmap")
        plt.xticks(rotation=90)
        plt.savefig(f"tmp/{league_name}.png")
    except RuntimeError as error:
        print ("ERROR: %s" % str(error))

