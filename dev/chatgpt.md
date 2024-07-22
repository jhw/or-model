You are a Python and scipy expert

Here is some Python code which implements an optimisation routine

```
from outrights.state import Event

import math, random

FactorMutationMultiplier=0.1

def mean(X):
    return sum(X)/len(X)

def kernel_1x2(match, ratings, factors, expfn):
    hometeamname, awayteamname = match["name"].split(" vs ")
    homerating=expfn(ratings[hometeamname])*factors["home_away_bias"]
    awayrating=expfn(ratings[awayteamname])/factors["home_away_bias"]
    ratio=homerating/(homerating+awayrating)
    drawprob=factors["draw_max"]+factors["draw_curvature"]*(ratio-0.5)**2
    return [ratio*(1-drawprob),
            drawprob,
            (1-ratio)*(1-drawprob)]

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

class Ratings(dict):
    
    def __init__(self, teamnames):
        dict.__init__(self)
        for teamname in teamnames:
            self[teamname]=random.gauss(0, 1)
            
    def normalise(self):
        mn=mean(self.values())
        for key in self.keys():
            self[key]-=mn
    
class RatingsSolver:
          
    def rms_error(self, X, Y):
        return (sum([(x-y)**2 
                     for x, y in zip(X, Y)])/len(X))**0.5
        
    def calc_1x2_error(self, matches, ratings, factors):
        probs=[kernel_1x2(match, ratings, factors, math.exp)
               for match in matches]
        errors=[self.rms_error(prob, Event(match).probabilities)
                for prob, match in zip(probs,
                                       matches)]
        return sum(errors)/len(matches)
    
    
    def mutate_team(self, matches, ratings, factors, 
                    decayfac, teamname, besterr):
        delta=random.gauss(0, 1)*decayfac
        # up
        ratings[teamname]+=delta
        err=self.calc_1x2_error(matches, ratings, factors)
        if err < besterr:
            return err
        # down
        ratings[teamname]-=2*delta # NB -=2*
        err=self.calc_1x2_error(matches, ratings, factors)
        if err < besterr:
            return err
        # reset
        ratings[teamname]+=delta
        return besterr
    
    def mutate_teams(self, matches, ratings, factors,
                     decayfac, err):
        for teamname in ratings.keys():
            err=self.mutate_team(matches, ratings, factors,
                                 decayfac, teamname, err)
        return err
    
    def mutate_factor(self, matches, ratings, factors,
                      decayfac, key, besterr):
        delta=random.gauss(0, 1)*decayfac*FactorMutationMultiplier
        # up
        factors[key]+=delta
        err=self.calc_1x2_error(matches, ratings, factors)
        if err < besterr:
            return err
        # down
        factors[key]-=2*delta
        if err < besterr:
            return err
        # reset
        factors[key]+=delta
        return besterr
    
    def mutate_factors(self, matches, ratings, factors, 
                       decayfac, err):
        for key in factors.keys():
            err=self.mutate_factor(matches, ratings, factors,
                                   decayfac, key, err)
        return err
    
    def solve(self, teamnames, matches, generations, decay, factors):
        ratings=Ratings(teamnames)
        err=self.calc_1x2_error(matches, ratings, factors)
        for i in range(generations):
            decayfac=((generations-i)/generations)**decay
            err=self.mutate_teams(matches, ratings, factors,
                                  decayfac, err)
            ratings.normalise()
            err=self.mutate_factors(matches, ratings, factors,
                                    decayfac, err)
        return (ratings, factors, err)
    
if __name__=="__main__":
    import json
    struct=json.loads(open("tmp/ENG1.json").read())
    teamnames=[team["name"] for team in struct["teams"]]
    trainingset=struct["events"]
    factors={"home_away_bias": 1.3,
             "draw_max": 0.3,
             "draw_curvature": -0.75}
    resp=RatingsSolver().solve(teamnames=teamnames,
                               matches=trainingset,
                               generations=250,
                               decay=2,
                               factors=factors)
    print (resp)

```

You give it data like this

```
{
  "teams": [
    {
      "name": "Arsenal"
    },
    {
      "name": "Aston Villa"
    },
    {
      "name": "Bournemouth"
    },
	{...}
  ],
  "events": [
    {
      "date": "2024-04-02",
      "name": "Bournemouth vs Crystal Palace",
      "prices": {
        "fd": [
          2.02,
          3.8,
          3.69
        ]
      }
    },
    {
      "date": "2024-04-02",
      "name": "Newcastle vs Everton",
      "prices": {
        "fd": [
          2.03,
          3.86,
          3.62
        ]
      }
    },
    {
      "date": "2024-04-02",
      "name": "Nott'm Forest vs Fulham",
      "prices": {
        "fd": [
          2.78,
          3.51,
          2.61
        ]
      }
    },
	{...}
  ]
}
```

And it returns this

```
({'Arsenal': 1.6877420853230083, 'Aston Villa': 0.1251897515429996, 'Bournemouth': -0.26287125968094643, 'Brentford': -0.4454131900015128, 'Brighton': -0.22135277682901483, 'Chelsea': 0.33142233200061044, 'Crystal Palace': -0.2631703505281464, 'Everton': -0.4573946511868617, 'Fulham': -0.18165905942451704, 'Ipswich': -0.6705256816360803, 'Leicester': -0.9489843224103225, 'Liverpool': 1.4646152632778435, 'Man City': 1.948503425222105, 'Man United': -0.04889632059296267, 'Newcastle': 0.22738536880007437, "Nott'm Forest": -0.6104924807233482, 'Southampton': -1.1224905743586975, 'Tottenham': 0.4872575653811498, 'West Ham': -0.3556694831330937, 'Wolves': -0.6831956410422867}, {'home_away_bias': 1.216972540520417, 'draw_max': 0.26342079987437517, 'draw_curvature': -0.8036243245101349}, 0.025406047476797537)
```

The first output represents ratings of different teams in a league, in an approximate (0, 1) normal space

The second are some optimised factors

The loss function is the difference between market observed probabilities for an event (home win, draw, away win) and model generated probabilities, calculated by passing random normal ratings to the 1x2 kernel function

I want you to replace the custom optimiser with a scipy one

I think you will have to do this in three passes

1) optimise the ratings of the teams in an approximate normal (0, 1) space given the initial factor guesses

2) tweak the value of the factors; these are not normal but are in unform space; they should not need to be tweaked more than +/- 0.1 in each case

3) re- optimise the team ratings based on the optimal factors

You may want to normalise the team ratings output, provided you don't think this affects the results

This is my suggestion for what you should do, but please feel free to suggest a better solution
