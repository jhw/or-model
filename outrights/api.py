from outrights.kernel import ScoreMatrix
from outrights.solver import RatingsSolver, Event
from outrights.simulator import SimPoints

def calc_league_table(team_names, results):
    # Initialize league table with team names
    league_table = {team_name: {'name': team_name,
                                'played': 0,
                                'points': 0,
                                'goal_difference': 0} for team_name in team_names}

    for result in results:
        home_team, away_team = result['name'].split(' vs ')
        home_score, away_score = result['score']

        # Update games played
        league_table[home_team]['played'] += 1
        league_table[away_team]['played'] += 1

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

def calc_training_errors(team_names, events, ratings, home_advantage):
    errors = {team_name: [] for team_name in team_names}
    for event in events:
        home_team_name, away_team_name = event["name"].split(" vs ")
        matrix = ScoreMatrix.initialise(event_name = event["name"],
                                        ratings = ratings,
                                        home_advantage = home_advantage)
        model_home_win, model_draw, model_away_win = [float(prob) for prob in matrix.match_odds]
        model_home_team_expected_points = 3 * model_home_win + model_draw
        model_away_team_expected_points = 3 * model_away_win + model_draw
        market_home_win, market_draw, market_away_win = Event(event).training_inputs
        market_home_team_expected_points = 3 * market_home_win + market_draw
        market_away_team_expected_points = 3 * market_away_win + market_draw        
        home_team_error = model_home_team_expected_points - market_home_team_expected_points
        away_team_error = model_away_team_expected_points - market_away_team_expected_points
        errors[home_team_name].append(home_team_error)
        errors[away_team_name].append(away_team_error)
    return errors


def calc_points_per_game_ratings(team_names, ratings, home_advantage):
    ppg_ratings = {team_name: 0 for team_name in team_names}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:
                event_name = f"{home_team_name} vs {away_team_name}"
                matrix = ScoreMatrix.initialise(event_name = event_name,
                                                ratings = ratings,
                                                home_advantage = home_advantage)
                home_win_prob, draw_prob, away_win_prob = [float(prob) for prob in matrix.match_odds]
                ppg_ratings[home_team_name] += 3 * home_win_prob + draw_prob
                ppg_ratings[away_team_name] += 3 * away_win_prob + draw_prob
    n_games = (len(team_names) - 1) * 2
    return {team_name:ppg_value / n_games
            for team_name, ppg_value in ppg_ratings.items()}

def calc_expected_season_points(team_names, results, remaining_fixtures, ratings, home_advantage):
    expected_points = {team["name"]: team["points"]
                       for team in calc_league_table(team_names = team_names,
                                                     results = results)}
    for event_name in remaining_fixtures:
        home_team_name, away_team_name = event_name.split(" vs ")
        matrix = ScoreMatrix.initialise(event_name = event_name,
                                        ratings = ratings,
                                        home_advantage = home_advantage)
        home_win_prob, draw_prob, away_win_prob = [float(prob) for prob in matrix.match_odds]
        expected_points[home_team_name] += 3 * home_win_prob + draw_prob
        expected_points[away_team_name] += 3 * away_win_prob + draw_prob
    return expected_points                                  

def mean(X):
    return sum(X)/len(X) if X != [] else 0

def variance(X):
    m = mean(X)
    return sum([(x-m)**2 for x in X])

def standard_deviation(X):
    return variance(X)**0.5

def simulate(team_names, training_set, results, rounds, n_paths):
    league_table = calc_league_table(team_names = team_names,
                                     results = results)
    remaining_fixtures = calc_remaining_fixtures(team_names = team_names,
                                                 results = results,
                                                 rounds = rounds)
    solver_resp = RatingsSolver().solve(team_names = team_names,
                                        events = training_set)
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
    training_errors = calc_training_errors(team_names = team_names,
                                           events = training_set,
                                           ratings = poisson_ratings,
                                           home_advantage = home_advantage)
    season_points = calc_expected_season_points(team_names = team_names,
                                                results = results,
                                                remaining_fixtures = remaining_fixtures,
                                                ratings = poisson_ratings,
                                                home_advantage = home_advantage)
    ppg_ratings = calc_points_per_game_ratings(team_names = team_names,
                                               ratings = poisson_ratings,
                                               home_advantage = home_advantage)
    for team in league_table:
        errors = training_errors[team["name"]]
        team.update({"training_events": len(errors),
                     "mean_training_error": mean(errors),
                     "std_training_error": standard_deviation(errors),
                     "poisson_rating": poisson_ratings[team["name"]],
                     "points_per_game_rating": ppg_ratings[team["name"]],
                     "expected_season_points": season_points[team["name"]],
                     "position_probabilities": position_probabilities[team["name"]]})
    return {"teams": league_table,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

if __name__=="__main__":
    pass
