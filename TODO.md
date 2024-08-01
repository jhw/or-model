### short [01-pricer]

- add a markets test to test.py

### medium

### thoughts

- why is std_training_error so high in many cases?

- why doesn't OU give a better fit?
  - is draw fitting a proxy for OU fit?
- better AH data?
  - from where?
- AH integer handicap fitting?
  - how?
- ability to constrain ratings?
  - not sure it's worth it
- remove sources dependency?
  - not sure it's worth it

### done

- add and filter markets.json
- pass markets to api
- calculate market groups
- calculate positions for each market group
- return Default group as position_probabilities
- value payoff
- assert payoff versus len(matrix)
- calculate and return marks
- remove positions properties
- test position matrix sums to one
- test event normalised probs
- test remaining fixtures
- ScoreMatrix.initialise should have default n arg
- convert all metrics to float
- mean, stdev of training_errors
- position heatmaps
- update league table
- training events
- 0.1.0
- season points
- test should not need to import Event
- split api into api and test 
- check for match refs
- check all arg passing uses named args
- move event from common
- rename common as kernel
- move fetch_leagues to api
- calc_remaining fixtures can just return name
- send match name to solver not match
- surface rounds argument
- change ratings output to be a teams table
- add SimPoints.simulate(fixtures)
- ensure (eg) ratings and error outputs are prefixed by solver 
- split simulator into simulator and API
- [chatgpt] non standard payoffs 
- simulator to return list for next team
- simulator noise
- position count matrix
- test argsort
- simulate goals consistent with matrix
- update table (points, goal difference)
- add initial state
- ScoreMatrix should not have default home_advantage
- remaining fixtures function
- results fetch
- pass date to solver and have it calculate league table and remaining fixtures
- OU fitting
- script to parse FD for AH, OU data
- remove fd key
- why doesn't fd scraper seem to be returning all events?
- expected points calculation
- fix stdev field
- poisson_solver disappointing results :(
- format existing solver results vs new scipy solver
- replace solver with scipy optimise [notes]
- add mean, sd training set errors to teams
- training set isn't cutting off properly at 6 teams
- add deductions
- return table.values()
- refactor api output
- remove seed
- allow drift multiplier to be part of output
- check result.xxx references
- leagues
- pass leaguename to test.py
- better directory structure
- better interfaces
- setup.py
- get simulator test to work
- abstract kernel

