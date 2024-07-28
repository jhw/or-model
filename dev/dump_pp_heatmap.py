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
        
        # Extract team names and position probabilities
        teams = [team['name'] for team in data['teams']]
        position_probabilities = [team['position_probabilities'] for team in data['teams']]
        
        # Calculate the sumproduct for each team
        position_indices = np.arange(1, len(teams) + 1)
        sumproduct_metrics = [np.dot(prob, position_indices) for prob in position_probabilities]
        
        # Sort teams and position probabilities based on the sumproduct metric
        sorted_teams_and_probs = sorted(zip(teams, position_probabilities, sumproduct_metrics), key=lambda x: x[2])
        sorted_teams, sorted_position_probabilities, _ = zip(*sorted_teams_and_probs)
        
        # Convert probabilities to percentages
        position_probabilities = np.array(sorted_position_probabilities) * 100
        
        # Apply square root transformation to intensify the color
        transformed_probabilities = np.sqrt(position_probabilities)
        
        # Plotting the heatmap
        plt.figure(figsize=(12, 12))
        heatmap = sns.heatmap(transformed_probabilities,
                              cmap='Reds',
                              yticklabels=sorted_teams,
                              xticklabels=np.arange(1, len(teams) + 1),
                              cbar=False)  # Remove color bar
        
        # Update title and add gap between title and heatmap
        plt.title(f"{league_name} Position Probability Heatmap", fontsize=20, pad=20)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=90)
        
        # Save the heatmap to a PNG file
        plt.savefig(f"tmp/{league_name}.png")
    
    except RuntimeError as error:
        print("ERROR: %s" % str(error))
