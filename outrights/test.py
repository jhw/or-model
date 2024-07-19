from outrights.helpers import fetch_teams, fetch_events, fetch_results

from outrights.api import generate

import sys

Markets=[{"league": "ENG2",
          "name": "Winner",
          "payoff": "1|23x0"}]

if __name__ == "__main__":
    leaguename="ENG2"
    teams=fetch_teams(leaguename)
    events=fetch_events(leaguename)
    results=fetch_results(leaguename)
    markets=[market for market in Markets
             if market["league"]==leaguename]
    resp=generate(leaguename=leaguename,
                  teams=teams,
                  events=events,
                  results=results,
                  markets=markets)
    import json
    print (json.dumps(resp,
                      indent=2))
