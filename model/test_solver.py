import model.solver as solver

import json, urllib.request

SolverParams={"seed": 22682,
              "generations": 250,
              "decay": 2,
              "factors": {"home_away_bias": 1.3,
                          "draw_max": 0.3,
                          "draw_curvature": -0.75}}

TrainingSetSize=6

def fetch_teams(leaguename,
                domainname="outrights.net"):
    url="https://teams.%s/list-teams?league=%s" % (domainname,
                                                   leaguename)
    return json.loads(urllib.request.urlopen(url).read())

class Event(dict):

    def __init__(self, event):
        dict.__init__(self, event)

    @property
    def best_prices(self, sources="fd|oc".split("|")):
        for source in sources:
            if source in self["prices"]:
                return self["prices"][source]
        return None
        
    @property
    def probabilities(self):                      
        probs=[1/price
               for price in self.best_prices]
        overround=sum(probs)
        return [prob/overround
                for prob in probs]
    
def fetch_events(leaguename,
                 domainname="outrights.net"):
    url="https://events.%s/list-events?league=%s" % (domainname,
                                                     leaguename)
    return [Event(event)
            for event in json.loads(urllib.request.urlopen(url).read())]
    
class Counter(dict):

    def __init__(self, teams):
        dict.__init__(self, {team["name"]:0
                             for team in teams})

    def add(self, event):
        for teamname in event["name"].split(" vs "):
            self[teamname]+=1

    def is_complete(self, limit):
        for k, v in self.items():
            if v < limit:
                return False
        return True

def filter_training_set(leaguename, teams, events, limit=TrainingSetSize):
    counter, trainingset = Counter(teams), []
    for event in reversed(sorted(events,
                                 key=lambda x: "%s/%s" % (x["date"],
                                                          x["name"]))):
        trainingset.append(event)
        counter.add(event)
        if counter.is_complete(limit):
            return trainingset
    if trainingset==[]:
        raise RuntimeError("%s no training set" % leaguename)
    return trainingset

if __name__=="__main__":
    leaguename="ENG2"
    teams, events = (fetch_teams(leaguename),
                     fetch_events(leaguename))
    trainingset=filter_training_set(leaguename=leaguename,
                                    teams=teams,
                                    events=events)
    request={"teamnames": [team["name"]
                           for team in teams],
             "trainingset": trainingset,
             "params": SolverParams}
    resp=solver.solve(**request)
    body=json.dumps(resp,
                    indent=2)
    metrics=dict(resp["factors"])
    metrics["error"]=resp["error"]
    print (body)
