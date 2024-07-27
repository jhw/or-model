import json, urllib.request

def fetch_leagues():
    return json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())
    
def filter_team_names(events):
    team_names = set()
    for event in events:
        for team_name in event["name"].split(" vs "):
            team_names.add(team_name)
    return sorted(list(team_names))

def calc_league_table(team_names, events):
    # Initialize league table with team names
    league_table = {team_name: {'name': team_name,
                                'games_played': 0,
                                'points': 0,
                                'goal_difference': 0} for team_name in team_names}

    for event in events:
        home_team, away_team = event['name'].split(' vs ')
        home_score, away_score = event['score']

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

def calc_remaining_fixtures(team_names, results, rounds=1):
    counts={}
    for home_team_name in team_names:
        for away_team_name in team_names:
            if home_team_name != away_team_name:    
                counts["%s vs %s" % (home_team_name, away_team_name)] = rounds
    for result in results:
        counts[result["name"]]-=1
    fixtures=[]
    for eventname, n in counts.items():
        for i in range(n):
            fixture = {"name": eventname}
            fixtures.append(fixture)
    return fixtures

if __name__=="__main__":
    pass
