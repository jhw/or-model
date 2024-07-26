import csv
import json
import requests
from datetime import datetime

UrlPattern = "https://www.football-data.co.uk/mmz4281/2324/%s.csv"

def fetch_events(league):
    url = UrlPattern % league["football-data-id"]

    response = requests.get(url)
    response.raise_for_status()

    decoded_content = response.content.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_content)

    events = []
    match_odds_sources = [
        ('Pinnacle', ['PSH', 'PSD', 'PSA']),
        ('bet365', ['B365H', 'B365D', 'B365A']),
        ('William Hill', ['WHH', 'WHD', 'WHA']),
        ('Ladbrokes', ['LBH', 'LBD', 'LBA'])
    ]
    
    asian_handicap_sources = [
        ('Pinnacle', ['PAHH', 'PAHA', 'AHh']),
        ('bet365', ['B365AHH', 'B365AHA', 'AHh']),
        ('Ladbrokes', ['LBAHH', 'LBAHA', 'AHh'])
    ]

    over_under_sources = [
        ('Pinnacle', ['P>2.5', 'P<2.5']),
        ('bet365', ['B365>2.5', 'B365<2.5'])
    ]

    for row in reader:
        event = {}
        event['name'] = f"{row['HomeTeam']} vs {row['AwayTeam']}"
        
        try:
            event['date'] = datetime.strptime(row['Date'], '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Date format not recognized for date: {row['Date']}")

        try:
            event['score'] = [int(row['FTHG']), int(row['FTAG'])]
        except ValueError:
            event['score'] = None
        
        match_odds = None
        asian_handicap = None
        over_under_25 = None

        # Match Odds
        for source, keys in match_odds_sources:
            if all(k in row and row[k] for k in keys):
                match_odds = {
                    'source': source,
                    'prices': [
                        float(row[keys[0]]),
                        float(row[keys[1]]),
                        float(row[keys[2]])
                    ]
                }
                break

        # Asian Handicap Odds
        for source, keys in asian_handicap_sources:
            if all(k in row and row[k] for k in keys):
                asian_handicap = {
                    'source': source,
                    'line': float(row[keys[2]]),
                    'prices': [
                        float(row[keys[0]]),
                        float(row[keys[1]])
                    ]
                }
                break

        # Over/Under 2.5 Goals
        for source, keys in over_under_sources:
            if all(k in row and row[k] for k in keys):
                over_under_25 = {
                    'source': source,
                    'prices': [
                        float(row[keys[0]]),
                        float(row[keys[1]])
                    ]
                }
                break

        event['match_odds'] = match_odds
        event['asian_handicap'] = asian_handicap
        event['over_under_25_goals'] = over_under_25
        events.append(event)

    return events

if __name__ == "__main__":
    try:
        import json, sys, urllib.request
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        leaguename = sys.argv[1]
        leagues = {league["name"]: league
                   for league in json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        league = leagues[leaguename]
        events = fetch_events(league)
        print(json.dumps(events[:3], indent=2))
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ValueError as error:
        print("Error: %s" % str(error))
