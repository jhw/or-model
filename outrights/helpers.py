import json, urllib.request

DomainName="outrights.net"

def fetch_leagues(domainname=DomainName):
    url="https://teams.%s/list-leagues" % domainname
    return json.loads(urllib.request.urlopen(url).read())

def fetch_teams(leaguename,
                domainname=DomainName):
    url="https://teams.%s/list-teams?league=%s" % (domainname,
                                                   leaguename)
    return json.loads(urllib.request.urlopen(url).read())
    
def fetch_events(leaguename,
                 domainname=DomainName):
    url="https://events.%s/list-events?league=%s" % (domainname,
                                                     leaguename)
    return json.loads(urllib.request.urlopen(url).read())

def fetch_results(leaguename,
                  domainname=DomainName):
    return []
    
