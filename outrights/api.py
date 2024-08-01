from outrights.kernel import ScoreMatrix
from outrights.markets import init_markets
from outrights.solver import RatingsSolver, Event
from outrights.simulator import SimPoints
from outrights.state import calc_league_table, calc_remaining_fixtures
from outrights.stats import mean, standard_deviation

def sum_product(X, Y):
    return sum([x*y for x, y in zip(X, Y)])

def calc_position_probabilities(sim_points, markets):
    position_probs = {"default": sim_points.position_probabilities()}
    for market in markets:
        if ("include" in market or
            "exclude" in market):
            position_probs[market["name"]] = sim_points.position_probabilities(teams_names = market["teams"])
    return position_probs

def calc_marks(position_probabilities, markets):
    marks = []
    for market in markets:
        position_probs_key = market["name"] if ("include" in market or "exclude" in market) else "default"
        position_probs = position_probabilities[position_probs_key]        
        for team_name in market["teams"]:
            mark_value = sum_product(position_probs[team_name], market["payoff"])
            mark = {"market": market["name"],
                    "team": team_name,
                    "mark": mark_value}
            marks.append(mark)
    return marks

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

def simulate(team_names, training_set, n_paths,
             results=[],
             markets=[],
             rounds=1):
    init_markets(team_names, markets)
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
                            home_advantage = home_advantage)
    position_probs = calc_position_probabilities(sim_points = sim_points,
                                                 markets = markets)
    marks = calc_marks(position_probabilities = position_probs,
                       markets = markets)
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
                     "position_probabilities": position_probs["default"][team["name"]]})
    return {"teams": league_table,
            "marks": marks,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

if __name__=="__main__":
    pass
