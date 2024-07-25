import csv
import json
import requests
from datetime import datetime

UrlPattern = "https://www.football-data.co.uk/mmz4281/2324/%s.csv"

def parse_football_data(league):
    url = UrlPattern % league["football-data-id"]

    response = requests.get(url)
    response.raise_for_status()

    decoded_content = response.content.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_content)

    events = []
    priority_sources = {
        'Pinnacle': ['PSH', 'PSD', 'PSA'],
        'bet365': ['B365H', 'B365D', 'B365A'],
        'William Hill': ['WHH', 'WHD', 'WHA'],
        'Ladbrokes': ['LBBH', 'LBBD', 'LBBA']  # Added mapping for Ladbrokes, assuming keys
    }

    for row in reader:
        event = {}
        event['name'] = f"{row['HomeTeam']} vs {row['AwayTeam']}"
        
        date_formats = ['%d/%m/%y', '%d/%m/%Y']
        for date_format in date_formats:
            try:
                event['date'] = datetime.strptime(row['Date'], date_format).strftime('%Y-%m-%d')
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Date format not recognized for date: {row['Date']}")
        
        match_odds = {}
        for source, keys in priority_sources.items():
            if keys[0] in row and row[keys[0]]:
                match_odds['source'] = source
                match_odds['prices'] = [
                    float(row[keys[0]]),
                    float(row[keys[1]]),
                    float(row[keys[2]])
                ]
                break
        
        if match_odds:  # Only add event if match odds are found
            event['match_odds'] = match_odds
            events.append(event)
    
    return json.dumps(events, indent=4)

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
        events = parse_football_data(league)
        for event in json.loads(events):
            print(event)
    except RuntimeError as error:
        print("Error: %s" % str(error))
    except ValueError as error:
        print("Error: %s" % str(error))
