def calc_league_table(team_names, results, handicaps):
    # Initialize league table with team names
    league_table = {team_name: {'name': team_name,
                                'played': 0,
                                'points': handicaps[team_name] if team_name in handicaps else 0,
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

def calc_remaining_fixtures(team_names, results, rounds = 1):
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

if __name__ == "__main__":
    pass
