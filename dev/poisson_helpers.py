import json, urllib.request

def fetch_leagues():
    return json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())
    
def filter_teamnames(events):
    teamnames = set()
    for event in events:
        for teamname in event["name"].split(" vs "):
            teamnames.add(teamname)
    return sorted(list(teamnames))

if __name__=="__main__":
    pass
