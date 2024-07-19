from outrights.helpers import fetch_leagues, fetch_teams, fetch_events, fetch_results

from outrights.api import generate

import re, sys

Markets=[{"league": "ENG2",
          "name": "Winner",
          "payoff": "1|23x0"},
         {"league": "ENG3",
          "name": "Winner",
          "payoff": "1|23x0"},
         {"league": "ENG4",
          "name": "Winner",
          "payoff": "1|23x0"}]

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        leaguename=sys.argv[1]
        leagues={league["name"]:league
                 for league in fetch_leagues()}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        teams=fetch_teams(leaguename)
        events=fetch_events(leaguename)
        results=fetch_results(leaguename)
        markets=[market for market in Markets
                 if market["league"]==leaguename]
        if markets==[]:
            raise RuntimeError("no markets found")
        resp=generate(leaguename=leaguename,
                      teams=teams,
                      events=events,
                      results=results,
                      markets=markets)
        import json
        print (json.dumps(resp,
                          indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
