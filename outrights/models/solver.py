from outrights.models import kernel_1x2

from outrights.state import Event

import math, random

FactorMutationMultiplier=0.1

def mean(X):
    return sum(X)/len(X)

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
    
def calc_ppg_ratings(teamnames, ratings, factors):
    ppg=dict([(teamname, 0)
              for teamname in teamnames])
    ngames=2*(len(teamnames)-1)
    for hometeamname in teamnames:
        for awayteamname in teamnames:
            if hometeamname==awayteamname:
                continue
            match={"name": "%s vs %s" % (hometeamname,
                                         awayteamname)}
            probs=kernel_1x2(match, ratings, factors, math.exp)
            ppg[hometeamname]+=3*probs[0]+probs[1]
            ppg[awayteamname]+=3*probs[-1]+probs[1]
    return dict([(key, value/ngames)
                 for key, value in ppg.items()])

def calc_fixture_probs(teamnames, ratings, factors):
    fixtures=[]
    for hometeamname in teamnames:
        for awayteamname in teamnames:
            if hometeamname==awayteamname:
                continue
            matchname="%s vs %s" % (hometeamname, awayteamname)
            probs=kernel_1x2({"name": matchname},
                                     ratings,
                                     factors,
                                     math.exp)
            fixture={"name": matchname,
                     "probabilities": probs}
            fixtures.append(fixture)
    return fixtures

def filter_training_set(trainingset, fixtures, teamname):
    fixtures={fixture["name"]:fixture
              for fixture in fixtures}
    items=[]
    for event in trainingset:
        matchteamnames=event["name"].split(" vs ")
        if teamname not in matchteamnames:
            continue
        marketprobs=Event(event).probabilities
        if abs(sum(marketprobs)-1) > 1e-5:
            raise RuntimeError("Market probs do not sum to 1")
        fixture=fixtures[event["name"]]
        modelprobs=fixture["probabilities"] 
        if abs(sum(modelprobs)-1) > 1e-5:
            raise RuntimeError("Model probs do not sum to 1")
        if teamname==matchteamnames[0]:
            homeaway, versus = "home", matchteamnames[1]
            marketexppoints=3*marketprobs[0]+marketprobs[1]
            modelexppoints=3*modelprobs[0]+modelprobs[1]
            error=modelexppoints-marketexppoints
        else:
            homeaway, versus = "away", matchteamnames[0]
            marketexppoints=3*marketprobs[2]+marketprobs[1]
            modelexppoints=3*modelprobs[2]+modelprobs[1]
            error=modelexppoints-marketexppoints
        item={"date": event["date"],
              "home_away": homeaway,
              "versus": versus,
              "market_pts": marketexppoints,
              "model_pts": modelexppoints,
              "error": error}
        items.append(item)
    return items

def solve(params, teamnames, trainingset):
    ratings, factors, error = RatingsSolver().solve(teamnames,
                                                    trainingset,
                                                    params["generations"],
                                                    params["decay"],
                                                    params["factors"])
    ppgratings=calc_ppg_ratings(teamnames, ratings, factors)
    fixtures=calc_fixture_probs(teamnames, ratings, factors)
    trainingsets={teamname: filter_training_set(trainingset,
                                                fixtures,
                                                teamname)
                  for teamname in teamnames}
    return {"ratings": ratings,
            "factors": factors,
            "error": error,
            "ppg_ratings": ppgratings,
            # "fixtures": fixtures, # no longer required by marks model
            "training_sets": trainingsets}

if __name__=="__main__":
    pass
