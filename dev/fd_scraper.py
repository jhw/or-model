"""
http://football-data.co.uk/notes.txt
"""

import csv
import datetime as dt
import io
import re
import urllib.error
import urllib.request

UrlPattern = "https://www.football-data.co.uk/mmz4281/%s/%s.csv"

def clean_text(text):
    return " ".join([tok for tok in re.split("\\s", text)
                     if tok != ''])

def http_get(url):
    return urllib.request.urlopen(url).read().decode("utf-8")


def filter_events(reader):
    def parse_date(text):
        day, month, year = [int(tok) for tok in text.split("/")]
        if year < 2000:
            year += 2000
        return dt.date(year, month, day).strftime("%Y-%m-%d")
    def filter_date(item):
        return parse_date(item["Date"])
    def filter_name(item):
        return "%s vs %s" % (item["HomeTeam"],
                             item["AwayTeam"])
    def filter_score(item):
        return [int(item["FTHG"]),
                int(item["FTAG"])]
    def filter_match_odds(item, bookmakers = ["PS", "B365", "LB", "WH"]):
        for bookmaker in bookmakers:
            prices = []
            for suffix in "HDA":
                attr = bookmaker + suffix
                if (attr in item
                    and item[attr] != ''):
                    prices.append(float(item[attr]))
            if len(prices) == 3:
                return {"prices": prices}
        return None
    def filter_asian_handicaps(item):
        prices = []
        for attr in ["PAHH", "PAHA"]:
            if (attr in item and
                item[attr] != ''):
                prices.append(float(item[attr]))
        line = float(item["AHh"]) if "AHh" in item else None
        if (len(prices) == 2 and
            line != None):                
            return {"prices": prices,
                    "line": line}
        else:
            return None
    def filter_over_under_goals(item, line = 2.5):
        prices = []
        for attr in [f"P>{line}", f"P<{line}"]:
            if (attr in item and
                item[attr] != ''):
                prices.append(float(item[attr]))
        if len(prices) == 2:
            return {"prices": prices,
                    "line": line}
        else:
            return None
    titles = next(reader)
    rows = [{title: clean_text(value)
             for title, value in zip(titles, row)}
            for row in reader]
    return [{k:v for k, v in item.items() if v}
            for item in [{"date": filter_date(row),
                          "name": filter_name(row),
                          "score": filter_score(row),
                          "match_odds": filter_match_odds(row),
                          "asian_handicaps": filter_asian_handicaps(row),
                          "over_under_goals": filter_over_under_goals(row)}
                         for row in rows]]

def parse_csv(text):
    return csv.reader(io.StringIO(text))

def fetch_events(league,
                 url_pattern = UrlPattern,
                 season = "2324"):
    url = url_pattern % (season, league["football-data-id"])
    return filter_events(parse_csv(http_get(url)))

if __name__ == "__main__":
    try:
        league = {"name": "ENG1",
                  "football-data-id": "E0"}
        events = fetch_events(league)
        import json
        with open("tmp/ENG1.json", 'w') as f:
            f.write(json.dumps(events,
                               indent = 2))
    except RuntimeError as error:
        print ("Error: %s" % str(error))

