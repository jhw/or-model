"""
- NB note that this function is also required by marks model and it's imperative that that it uses the same code
"""

def kernel_1x2(match, ratings, factors, expfn):
    hometeamname, awayteamname = match["name"].split(" vs ")
    homerating=expfn(ratings[hometeamname])*factors["home_away_bias"]
    awayrating=expfn(ratings[awayteamname])/factors["home_away_bias"]
    ratio=homerating/(homerating+awayrating)
    drawprob=factors["draw_max"]+factors["draw_curvature"]*(ratio-0.5)**2
    return [ratio*(1-drawprob),
            drawprob,
            (1-ratio)*(1-drawprob)]
