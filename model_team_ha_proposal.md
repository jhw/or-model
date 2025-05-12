# Team-Specific Home Advantage Implementation Proposal

## Summary
This proposal outlines the implementation of team-specific home advantages in the OR-model, replacing the current global home advantage parameter with individual parameters for each team.

## Motivation
The current model uses a single home advantage factor for all teams, but real-world data suggests home advantage varies significantly between teams. Some teams perform substantially better at home, while others show minimal home/away performance differential. Implementing team-specific home advantages will improve model accuracy and provide more nuanced predictions.

## Implementation Changes

### 1. Data Structure Changes

Replace the scalar `home_advantage` with a dictionary mapping team names to their specific home advantage values:

```python
# Before
home_advantage = 1.25  # Single value for all teams

# After
home_advantages = {
    "Team A": 1.35,
    "Team B": 1.18,
    "Team C": 1.29,
    # ... entries for all teams
}
```

### 2. Required Code Modifications

#### `kernel.py` Changes

Modify the `ScoreMatrix.initialise` method to accept team-specific home advantages:

```python
@classmethod
def initialise(self, event_name, ratings, home_advantages, n=11, rho=0.1):
    home_team_name, away_team_name = event_name.split(" vs ")
    # Use team-specific home advantage instead of global value
    home_lambda = ratings[home_team_name] * home_advantages[home_team_name]
    away_lambda = ratings[away_team_name]
    return ScoreMatrix(home_lambda, away_lambda, n, rho)
```

#### `solver.py` Changes

1. Modify `RatingsSolver.calc_error` to work with home advantage dictionary:

```python
def calc_error(self, events, ratings, home_advantages):
    matrices = [ScoreMatrix.initialise(event_name=event["name"],
                                      ratings=ratings,
                                      home_advantages=home_advantages)
               for event in events]        
    errors = [self.rms_error(self.model_selector(event=event, matrix=matrix),
                            self.market_selector(event))
             for event, matrix in zip(events, matrices)]
    return np.mean(errors)
```

2. Add a new optimization method for team-specific home advantages:

```python
def optimise_ratings_and_team_advantages(self, events, ratings, max_iterations,
                                       rating_range=RatingRange,
                                       bias_range=HomeAdvantageRange):
    team_names = sorted(list(ratings.keys()))
    
    # Initialize parameters: first all team ratings, then all home advantages
    optimiser_ratings = [ratings[team_name] for team_name in team_names]
    # Initialize all home advantages to the middle of the range
    optimiser_advantages = [sum(bias_range) / 2 for _ in team_names]
    optimiser_bounds = [rating_range] * len(optimiser_ratings) + [bias_range] * len(team_names)
    optimiser_params = optimiser_ratings + optimiser_advantages

    def objective(params):
        # Update ratings
        for i, team in enumerate(team_names):
            ratings[team] = params[i]
        
        # Update home advantages
        home_advantages = {}
        for i, team in enumerate(team_names):
            home_advantages[team] = params[i + len(team_names)]
            
        return self.calc_error(events=events,
                              ratings=ratings,
                              home_advantages=home_advantages)

    result = minimize(objective,
                     optimiser_params,
                     method='L-BFGS-B',
                     bounds=optimiser_bounds,
                     options={'maxiter': max_iterations})
    
    # Extract optimized values
    for i, team in enumerate(team_names):
        ratings[team] = result.x[i]
    
    # Return team-specific home advantages
    home_advantages = {}
    for i, team in enumerate(team_names):
        home_advantages[team] = result.x[i + len(team_names)]
        
    return home_advantages
```

3. Update the `solve` method to support team-specific home advantages:

```python
def solve(self, events, ratings,
         home_advantages=None,
         max_iterations=100):
    if home_advantages:
        self.optimise_ratings(events=events,
                             ratings=ratings,
                             home_advantages=home_advantages,
                             max_iterations=max_iterations)
    else:
        home_advantages = self.optimise_ratings_and_team_advantages(events=events,
                                                                  ratings=ratings,
                                                                  max_iterations=max_iterations)
    error = self.calc_error(events=events,
                           ratings=ratings,
                           home_advantages=home_advantages)
    return {"ratings": {k: float(v) for k, v in ratings.items()},
            "home_advantages": {k: float(v) for k, v in home_advantages.items()},
            "error": float(error)}
```

#### `simulator.py` Changes

Update the `simulate` method to use team-specific home advantages:

```python
def simulate(self, event_name, ratings, home_advantages):    
    matrix = ScoreMatrix.initialise(event_name=event_name,
                                   ratings=ratings,
                                   home_advantages=home_advantages)
    scores = matrix.simulate_scores(self.n_paths)
    self.update_event(event_name, scores)
```

#### `main.py` Changes

Update all functions that use home advantage to work with the dictionary:

```python
def calc_training_errors(team_names, events, ratings, home_advantages):
    errors = {team_name: [] for team_name in team_names}
    for event in events:
        home_team_name, away_team_name = event["name"].split(" vs ")
        matrix = ScoreMatrix.initialise(event_name=event["name"],
                                       ratings=ratings,
                                       home_advantages=home_advantages)
        # ...rest of function stays the same
```

Similar updates would be needed for:
- `calc_points_per_game_ratings`
- `calc_expected_season_points`
- `simulate`

### 3. Backward Compatibility (Optional)

To maintain backward compatibility with code that expects a single home advantage value:

```python
def ensure_home_advantages_dict(team_names, home_advantage_input):
    """Convert a single home advantage value to a team dictionary if needed"""
    if isinstance(home_advantage_input, dict):
        return home_advantage_input
    else:
        # Create a dictionary with the same value for all teams
        return {team_name: home_advantage_input for team_name in team_names}
```

## Benefits and Expected Improvements

1. **Improved Model Accuracy**: Capture team-specific home advantage variations.
2. **Better Predictions**: More accurate forecasts of match outcomes and season-long projections.
3. **Enhanced Insights**: Ability to quantify and compare home advantage across teams.
4. **Market Advantage**: More accurate odds for teams with unusual home/away performance patterns.

## Challenges and Considerations

1. **Increased Parameter Space**: Adding n parameters (one per team) increases risk of overfitting.
2. **Data Requirements**: Need sufficient home matches per team to reliably estimate parameters.
3. **Regularization**: May need regularization to prevent extreme values.
4. **New Teams**: Need to handle teams with no history (could use league average).

## Implementation Plan

1. Create backward-compatible interfaces so existing code continues working.
2. Implement core changes to kernel.py and solver.py.
3. Update remaining code to use team-specific home advantages.
4. Develop fallback mechanisms for insufficient data scenarios.
5. Add regularization if necessary to ensure stable parameter values.
6. Develop visualization tools to compare team home advantages.

## Validation Methods

1. Cross-validation to ensure improved predictions.
2. Compare model error before and after implementation.
3. Analyze the distribution of team-specific home advantages against expectations.
4. Test with various league datasets to ensure robustness.

## Conclusion

Implementing team-specific home advantages should improve model accuracy with minimal changes to the core architecture. The expected performance improvements justify the added complexity, especially for leagues where home advantage varies significantly between teams.