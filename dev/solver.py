from outrights.state import Event

import json, math, random

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
        return {"ratings": dict(ratings),
                "factors": dict(factors),
                "error": err}
    
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
    print (json.dumps(resp,
                      sort_keys=True,
                      indent=2))
