from outrights.helpers import fetch_leagues, fetch_teams, fetch_events

import os, re, sys

if __name__ == "__main__":
    try:
        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        leaguename=sys.argv[1]
        leagues={league["name"]:league
                 for league in fetch_leagues()}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        teams=fetch_teams(leaguename)
        events=fetch_events(leaguename)
        struct={"teams": teams,
                "events": events}
        import json
        with open("tmp/%s.json" % leaguename, 'w') as f:
            f.write(json.dumps(struct,
                               indent=2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))
