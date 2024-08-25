def parse_payoff(payoff_expr):
    payoff=[]
    for expr in payoff_expr.split("|"):
        tokens=[float(tok) # championship playoffs 0.25
                for tok in expr.split("x")]
        if len(tokens)==1:            
            n, v = 1, tokens[0]
        else:
            n, v = tokens
        for i in range(int(n)):
            payoff.append(v)
    return payoff

def init_payoff(fn):
    def wrapped(team_names, market):
        fn(team_names, market)
        market["payoff"] = parse_payoff(market["payoff"])
        if len(market["payoff"]) != len(market["teams"]):
            raise RuntimeError("%s teams/payoff mismatch" % market["name"])
    return wrapped
        
@init_payoff        
def init_include_market(team_names, market):
    unknown = [team_name for team_name in market["include"]
               if team_name not in team_names]
    if unknown != []:
        raise RuntimeError("%s market has unknown teams %s" % (market["name"], ", ".join(unknown)))
    market["teams"] = market["include"]

@init_payoff
def init_exclude_market(team_names, market):
    unknown = [team_name for team_name in market["exclude"]
               if team_name not in team_names]
    if unknown != []:
        raise RuntimeError("%s market has unknown teams %s" % (market["name"], ", ".join(unknown)))
    market["teams"] = [team_name for team_name in team_names
                       if team_name not in market["exclude"]]

@init_payoff
def init_market(team_names, market):
    market["teams"] = team_names
        
def init_markets(team_names, markets):
    for market in markets:
        if "include" in market:
            init_include_market(team_names, market)
        elif "exclude" in market:
            init_exclude_market(team_names, market)
        else:
            init_market(team_names, market)
            
if __name__ == "__main__":
    pass
