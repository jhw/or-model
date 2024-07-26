import json, urllib.request

def fetch_leagues():
    return json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())
    
def filter_teamnames(events):
    teamnames = set()
    for event in events:
        for teamname in event["name"].split(" vs "):
            teamnames.add(teamname)
    return sorted(list(teamnames))

def calc_league_table(events):
    league_table = {}

    for event in events:
        home_team, away_team = event['name'].split(' vs ')
        home_score, away_score = event['score']

        if home_team not in league_table:
            league_table[home_team] = {'name': home_team, 'games_played': 0, 'points': 0, 'goal_difference': 0}
        if away_team not in league_table:
            league_table[away_team] = {'name': away_team, 'games_played': 0, 'points': 0, 'goal_difference': 0}

        league_table[home_team]['games_played'] += 1
        league_table[away_team]['games_played'] += 1

        goal_difference = home_score - away_score
        league_table[home_team]['goal_difference'] += goal_difference
        league_table[away_team]['goal_difference'] -= goal_difference

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
