from poisson_kernel import ScoreMatrix
from poisson_solver import RatingsSolver
from poisson_simulator import SimPoints

def calc_league_table(team_names, results):
    # Initialize league table with team names
    league_table = {team_name: {'name': team_name,
                                'games_played': 0,
                                'points': 0,
                                'goal_difference': 0} for team_name in team_names}

    for result in results:
        home_team, away_team = result['name'].split(' vs ')
        home_score, away_score = result['score']

        # Update games played
        league_table[home_team]['games_played'] += 1
        league_table[away_team]['games_played'] += 1

        # Update goal difference
        goal_difference = home_score - away_score
        league_table[home_team]['goal_difference'] += goal_difference
        league_table[away_team]['goal_difference'] -= goal_difference

        # Update points
        if home_score > away_score:
            league_table[home_team]['points'] += 3
        elif away_score > home_score:
            league_table[away_team]['points'] += 3
        else:
            league_table[home_team]['points'] += 1
            league_table[away_team]['points'] += 1

    # Convert to a list and sort by points and then by goal difference
    league_table_list = sorted(league_table.values(), key=lambda x: (x['points'], x['goal_difference']), reverse=True)

    return league_table_list

def calc_remaining_fixtures(team_names, results, rounds):
    counts={}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:    
                counts[f"{home_team_name} vs {away_team_name}"] = rounds
    for result in results:
        counts[result["name"]]-=1
    event_names = []
    for event_name, n in counts.items():
        for i in range(n):
            event_names.append(event_name)
    return event_names

def calc_ppg_ratings(team_names, ratings, home_advantage):
    ppg_ratings = {team_name: 0 for team_name in team_names}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:
                event_name = f"{home_team_name} vs {away_team_name}"
                matrix = ScoreMatrix.initialise(event_name = event_name,
                                                ratings = ratings,
                                                home_advantage = home_advantage)
                home_win_prob, draw_prob, away_win_prob = matrix.match_odds
                ppg_ratings[home_team_name] += 3 * home_win_prob + draw_prob
                ppg_ratings[away_team_name] += 3 * away_win_prob + draw_prob
    n_games = (len(team_names) - 1) * 2
    return {team_name:ppg_value / n_games
            for team_name, ppg_value in ppg_ratings.items()}

def simulate(team_names, training_set, results, rounds, n_paths):
    league_table = sorted(calc_league_table(team_names = team_names,
                                            results = results),
                          key = lambda x: x["name"])                        
    remaining_fixtures = calc_remaining_fixtures(team_names = team_names,
                                                 results = results,
                                                 rounds = rounds)
    solver_resp = RatingsSolver().solve(team_names = team_names,
                                        matches = training_set)
    poisson_ratings = solver_resp["ratings"]
    home_advantage = solver_resp["home_advantage"]
    solver_error = solver_resp["error"]
    sim_points = SimPoints(league_table, n_paths)
    for event_name in remaining_fixtures:
        sim_points.simulate(event_name = event_name,
                            ratings = poisson_ratings,
                            home_advantage = home_advantage,
                            n_paths = n_paths)
    position_probabilities = sim_points.position_probabilities
    ppg_ratings = calc_ppg_ratings(team_names = team_names,
                                   ratings = poisson_ratings,
                                   home_advantage = home_advantage)
    teams = [{"name": team_name,
              "poisson_rating": poisson_ratings[team_name],
              "ppg_rating": ppg_ratings[team_name],
              "position_probabilities": position_probabilities[team_name]}
             for team_name in team_names]
    return {"teams": teams,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

if __name__=="__main__":
    pass