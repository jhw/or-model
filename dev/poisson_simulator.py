from poisson_common import ScoreMatrix
from poisson_solver import RatingsSolver, Event
from poisson_helpers import fetch_leagues, filter_teamnames, calc_league_table

import fd_scraper as fd

if __name__=="__main__":
    try:
        import re, sys
        if len(sys.argv) < 4:
            raise RuntimeError("please enter league, cutoff, n_events")
        leaguename, cutoff, n_events = sys.argv[1:4]
        if not re.search("^\\D{3}\\d$", leaguename):
            raise RuntimeError("league is invalid")
        if not re.search("^\\d{4}\\-\\d{2}\\-\\d{2}$", cutoff):
            raise RuntimeError("cutoff is invalid")
        if not re.search("^\\d+$", n_events):
            raise RuntimeError("n_events is invalid")
        n_events = int(n_events)
        print ("fetching leagues")
        leagues={league["name"]: league
                 for league in fetch_leagues()}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        print ("fetching events")
        events = [Event(event)
                  for event in fd.fetch_events(leagues[leaguename])
                  if event["date"] <= cutoff]
        if events == []:
            raise RuntimeError("no events found")
        print ("%i events" % len(events))
        teamnames = filter_teamnames(events)
        print ("%i teams" % len(teamnames))
        """
        trainingset = sorted(events,
                             key = lambda e: e["date"])[-n_events:]
        print ("%s training set events [%s -> %s]" % (len(trainingset),
                                                   trainingset[0]["date"],
                                                   trainingset[-1]["date"]))
        resp = RatingsSolver().solve(teamnames=teamnames, matches=trainingset)
        print (resp)
        """
        table = calc_league_table(teamnames, events)
        print (table)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
