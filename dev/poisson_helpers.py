import json, urllib.request

def fetch_leagues():
    return json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())
    
def filter_teamnames(events):
    teamnames = set()
    for event in events:
        for teamname in event["name"].split(" vs "):
            teamnames.add(teamname)
    return sorted(list(teamnames))

def calc_league_table(teamnames, events):
    # Initialize league table with team names
    league_table = {team: {'name': team, 'games_played': 0, 'points': 0, 'goal_difference': 0} for team in teamnames}

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

if __name__=="__main__":
    pass
