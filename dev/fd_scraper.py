"""
http://football-data.co.uk/notes.txt
"""

import csv, datetime, io, json, re, urllib.request

UrlPattern="https://www.football-data.co.uk/mmz4281/2324/%s.csv"

def clean_text(text):
    return " ".join([tok for tok in re.split("\\s", text)
                     if tok!=''])

def http_get(url):
    return urllib.request.urlopen(url).read().decode("utf-8")

def filter_events(reader):
    def parse_date(text):
        day, month, year = [int(tok) for tok in text.split("/")]
        if year < 2000:
            year+=2000
        return datetime.date(year, month, day).strftime("%Y-%m-%d")
    def filter_date(item):
        return parse_date(item["Date"])
    def filter_name(item):
        return "%s vs %s" % (item["HomeTeam"],
                             item["AwayTeam"])
    def filter_prices(item, prefixes=["PS", "B365", "LB", "WH"]):
        for prefix in prefixes:
            prices=[]
            for suffix in "HDA":
                attr=prefix+suffix
                if (attr in item
                    and item[attr]!=''):
                    prices.append(float(item[attr]))
            if len(prices)==3:
                return prices
        return None # occasionally prices are completely blank
    titles=next(reader)
    rows=[{title: clean_text(value)
           for title, value in zip(titles, row)}
          for row in reader]
    return [item for item in [{"date": filter_date(row),
                               "name": filter_name(row),
                               "prices": filter_prices(row)}
                              for row in rows]
            if item["prices"]]

def parse_csv(text):
    return csv.reader(io.StringIO(text))

def fetch_events(league,
                 urlpattern=UrlPattern,
                 dgf_window=["2024-04-01", "2024-07-01"], # Don't Give a Fuck
                 cutoff="2024-01-01",
                 **kwargs):
    url=urlpattern % league["football-data-id"]
    return [event for event in filter_events(parse_csv(http_get(url)))
            if (event["date"] >= cutoff and
                not (event["date"] >= dgf_window[0] and
                     event["date"] < dgf_window[1]))]

if __name__=="__main__":
    try:
        import json, sys, urllib.request
        if len(sys.argv) < 2:
            raise RuntimeError("please enter league")
        leaguename=sys.argv[1]
        leagues={league["name"]: league
                for league in json.loads(urllib.request.urlopen("https://teams.outrights.net/list-leagues").read())}
        if leaguename not in leagues:
            raise RuntimeError("league not found")
        for event in fetch_events(leagues[leaguename]):
            print (event)            
    except RuntimeError as error:
        print ("Error: %s" % str(error))

