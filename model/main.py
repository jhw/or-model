from model.kernel import ScoreMatrix
from model.markets import init_markets
from model.solver import RatingsSolver
from model.simulator import SimPoints
from model.state import calc_league_table, calc_remaining_fixtures

def mean(X):
    return sum(X) / len(X) if X != [] else 0

def variance(X):
    m = mean(X)
    return sum([(x - m) ** 2 for x in X])

def std_deviation(X):
    return variance(X) ** 0.5

class Event(dict):

    def __init__(self, event):
        dict.__init__(self, event)

    def probabilities(self, attr):
        probs = [1 / price for price in self[attr]["prices"]]
        overround = sum(probs)
        return [prob / overround for prob in probs]

    @property
    def match_odds(self):
        return self.probabilities("match_odds")

    @property
    def expected_home_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[0] + match_odds[1]

    @property
    def expected_away_points(self):
        match_odds = self.match_odds
        return 3 * match_odds[2] + match_odds[1]

def calc_training_errors(team_names, events, ratings, home_advantage):
    errors = {team_name: [] for team_name in team_names}
    for event in events:

        home_team_name, away_team_name = event["name"].split(" vs ")
        matrix = ScoreMatrix.initialise(event_name = event["name"],
                                        ratings = ratings,
                                        home_advantage = home_advantage)
        event = Event(event)
        home_team_err = matrix.expected_home_points - event.expected_home_points
        away_team_err = matrix.expected_away_points - event.expected_away_points
        errors[home_team_name].append(home_team_err)
        errors[away_team_name].append(away_team_err)
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
                ppg_ratings[home_team_name] += matrix.expected_home_points
                ppg_ratings[away_team_name] += matrix.expected_away_points
    n_games = (len(team_names) - 1) * 2
    return {team_name:ppg_value / n_games
            for team_name, ppg_value in ppg_ratings.items()}

def calc_expected_season_points(team_names, results, handicaps, remaining_fixtures, ratings, home_advantage):
    exp_points = {team["name"]: team["points"]
                  for team in calc_league_table(team_names = team_names,
                                                results = results,
                                                handicaps = handicaps)}
    for event_name in remaining_fixtures:
        home_team_name, away_team_name = event_name.split(" vs ")
        matrix = ScoreMatrix.initialise(event_name = event_name,
                                        ratings = ratings,
                                        home_advantage = home_advantage)
        exp_points[home_team_name] += matrix.expected_home_points
        exp_points[away_team_name] += matrix.expected_away_points
    return exp_points                                  

def calc_position_probabilities(sim_points, markets):
    position_probs = {"default": sim_points.position_probabilities()}
    for market in markets:
        if ("include" in market or
            "exclude" in market):
            position_probs[market["name"]] = sim_points.position_probabilities(team_names = market["teams"])
    return position_probs

def sum_product(X, Y):
    return sum([x*y for x, y in zip(X, Y)])

def calc_outright_marks(position_probabilities, markets):
    marks = []
    for market in markets:
        group_pp_key = market["name"] if ("include" in market or "exclude" in market) else "default"
        group_pp_matrix = position_probabilities[group_pp_key]        
        for team_name in market["teams"]:
            mark_value = sum_product(group_pp_matrix[team_name],
                                     market["payoff"])
            mark = {"market": market["name"],
                    "team": team_name,
                    "mark": mark_value}
            marks.append(mark)
    return marks

def simulate(ratings,
             training_set,
             model_selector,
             market_selector,
             max_iterations = 100,
             n_paths = 1000,
             results = [],
             handicaps = {},
             markets = [],
             rounds = 1):
    team_names = sorted(list(ratings.keys()))
    init_markets(team_names, markets)
    league_table = calc_league_table(team_names = team_names,
                                     results = results,
                                     handicaps = handicaps)
    remaining_fixtures = calc_remaining_fixtures(team_names = team_names,
                                                 results = results,
                                                 rounds = rounds)
    solver = RatingsSolver(model_selector = model_selector,
                           market_selector = market_selector)
    solver_resp = solver.solve(ratings = ratings,
                               events = training_set,
                               max_iterations = max_iterations)
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
    training_errors = calc_training_errors(team_names = team_names,
                                           events = training_set,
                                           ratings = poisson_ratings,
                                           home_advantage = home_advantage)
    season_points = calc_expected_season_points(team_names = team_names,
                                                results = results,
                                                handicaps = handicaps,
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
                     "std_training_error": std_deviation(errors),
                     "poisson_rating": poisson_ratings[team["name"]],
                     "points_per_game_rating": ppg_ratings[team["name"]],
                     "expected_season_points": season_points[team["name"]],
                     "position_probabilities": position_probs["default"][team["name"]]})
    outright_marks = calc_outright_marks(position_probabilities = position_probs,
                                         markets = markets)        
    return {"teams": league_table,
            "outright_marks": outright_marks,
            "home_advantage": home_advantage,
            "solver_error": solver_error}

if __name__=="__main__":
    pass
