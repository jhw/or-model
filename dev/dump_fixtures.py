import json
import re
import sys
import urllib.request

import json, urllib.request

DomainName = "outrights.net"

def fetch_events(league_name,
                 domain_name = DomainName):
    url = f"https://events.{domain_name}/list-events?league={league_name}"
    return json.loads(urllib.request.urlopen(url).read())

def fetch_results(league_name,
                  domain_name = DomainName):
    url = f"https://results.{domain_name}/list-results?league={league_name}"
    return json.loads(urllib.request.urlopen(url).read())


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        league_name = sys.argv[1]
        if not re.search("^\\D{3}\\d{1}", league_name):
            raise RuntimeError("league is invalid")
        results = [{"name": result["name"],
                    "date": result["date"],
                    "score": result["scores"]["fd"]}
                   for result in fetch_results(league_name)
                   if "fd" in result["scores"]]
        results_map = {f"{result['name']}/{result['date']}": result
                       for result in results}
        events = fetch_events(league_name)
        for event in events:
            key = f"{event['name']}/{event['date']}"
            if key not in results_map:
                continue
            result = results_map[key]
            result["match_odds"] = {"prices": event["match_odds"]["prices"]["fd"]}
        with open(f"fixtures/{league_name}.json", 'w') as f:
            f.write(json.dumps(sorted(results,
                                      key = lambda x: f"{x['date']}/{x['name']}"),
                               indent = 2))
    except RuntimeError as error:
        print(f"Error: {error}")
