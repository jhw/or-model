from poisson_kernel import ScoreMatrix

import numpy as np

import random

class SimPoints:

    GDMultiplier = 1e-4

    NoiseMultiplier = 1e-8
    
    def __init__(self, league_table, n_paths):
        self.n_paths = n_paths
        self.team_names = [team["name"] for team in league_table]
        self.points = self._init_points_array(league_table)

    def _init_points_array(self, league_table):
        points_array = np.zeros((len(league_table), self.n_paths))
        for i, team in enumerate(league_table):
            points_with_goal_diff_and_noise = team['points'] + self.GDMultiplier * team['goal_difference'] + self.NoiseMultiplier * (random.random()-0.5)
            points_array[i, :] = points_with_goal_diff_and_noise
        return points_array

    def get_team_points(self, team_name):
        team_index = self.team_names.index(team_name)
        return self.points[team_index]

    def simulate(self, event_name, ratings, home_advantage, n_paths):    
        matrix = ScoreMatrix.initialise(event_name = event_name,
                                        ratings = ratings,
                                        home_advantage = home_advantage)
        scores = matrix.simulate_points(n_paths)
        self.update_event(event_name, scores)
    
    def update_home_team(self, team_name, scores):
        points = np.array([3*int(score[0] > score[1]) + int(score[0] == score[1])
                           for score in scores])
        goal_difference = np.array([score[0]-score[1] for score in scores])
        team_index = self.team_names.index(team_name)
        self.points[team_index] += points + self.GDMultiplier * goal_difference

    def update_away_team(self, team_name, scores):
        points = np.array([3*int(score[1] > score[0]) + int(score[0] == score[1])
                           for score in scores])
        goal_difference = np.array([score[1]-score[0] for score in scores])
        team_index = self.team_names.index(team_name)
        self.points[team_index] += points + self.GDMultiplier * goal_difference

    def update_event(self, event_name, scores):
        home_team_name, away_team_name = event_name.split(" vs ")
        self.update_home_team(home_team_name, scores)
        self.update_away_team(away_team_name, scores)

    @property
    def positions(self):
        return len(self.points) - np.argsort(np.argsort(self.points, axis=0), axis=0) - 1

    @property
    def position_probabilities(self):
        counts = np.zeros((len(self.points), len(self.points)))
        for i, row in enumerate(self.positions):
            for j in row:
                counts[i][j] += 1
        probabilities = counts / self.n_paths
        return {team_name:[float(value) for value in list(row)]
                for team_name, row in zip(self.team_names, probabilities)}
    
if __name__=="__main__":
    pass
