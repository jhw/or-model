# Team-Specific Additive Home Advantage Proposal

## Background

The or-model currently uses a global multiplicative home advantage factor that applies to all teams:

```python
home_lambda = ratings[home_team_name] * home_advantage
```

Our previous proposal outlined changing this to an additive model:

```python
home_lambda = ratings[home_team_name] + home_advantage
```

This proposal extends the additive model to implement team-specific home advantages, where each team has its own home advantage parameter.

## Proposed Changes

1. Replace the global additive home advantage with team-specific values
2. Implement an optimization strategy to solve for these individual home advantages
3. Maintain appropriate constraints to ensure reasonable home advantage distributions

## Implementation Plan

### 1. Modify `kernel.py` to Support Team-Specific Home Advantages

Update the `ScoreMatrix.initialise` method:

```python
@classmethod
def initialise(self, event_name, ratings, home_advantage, n=11, rho=0.1):
    home_team_name, away_team_name = event_name.split(" vs ")
    
    # Handle both dictionary and scalar home_advantage for backward compatibility
    if isinstance(home_advantage, dict):
        # Get team-specific home advantage (with fallback to average)
        team_ha = home_advantage.get(home_team_name, 0.3)  # Default to 0.3 if not found
    else:
        # Use global home advantage value
        team_ha = home_advantage
        
    # Use additive home advantage
    home_lambda = ratings[home_team_name] + team_ha
    away_lambda = ratings[away_team_name]
    
    return ScoreMatrix(home_lambda, away_lambda, n, rho)
```

### 2. Extend `solver.py` to Optimize Team-Specific Home Advantages

Add new constants:

```python
RatingRange = (0, 6)
HomeAdvantageRange = (0, 0.5)  # Additive range in goals
MinimumMatchesForTeamHA = 5  # Minimum home matches needed for team-specific HA
```

Modify the `calc_error` method to handle team-specific home advantages:

```python
def calc_error(self, events, ratings, home_advantage):
    matrices = [ScoreMatrix.initialise(event_name=event["name"],
                                      ratings=ratings,
                                      home_advantage=home_advantage)
               for event in events]        
    errors = [self.rms_error(self.model_selector(event=event,
                                               matrix=matrix),
                           self.market_selector(event))
             for event, matrix in zip(events, matrices)]
    return np.mean(errors)
```

Add a new method for optimizing team-specific home advantages:

```python
def optimise_team_home_advantages(self, events, ratings, home_advantages, max_iterations,
                                 advantage_range=HomeAdvantageRange,
                                 min_matches=MinimumMatchesForTeamHA):
    # Get list of teams with enough home matches for team-specific HA
    home_match_counts = {}
    for event in events:
        home_team = event["name"].split(" vs ")[0]
        home_match_counts[home_team] = home_match_counts.get(home_team, 0) + 1
    
    # Only optimize HAs for teams with sufficient data
    teams_for_ha_opt = [team for team, count in home_match_counts.items() 
                        if count >= min_matches]
    
    # Use global average for teams with insufficient data
    global_ha = sum(home_advantages.values()) / len(home_advantages) if home_advantages else 0.3
    
    # Create initial parameter array and bounds
    optimiser_advantages = [home_advantages.get(team, global_ha) for team in teams_for_ha_opt]
    optimiser_bounds = [advantage_range] * len(optimiser_advantages)
    
    def objective(params):
        # Update home_advantages with optimized values
        for i, team in enumerate(teams_for_ha_opt):
            home_advantages[team] = params[i]
        
        # Use global average for any teams not being optimized
        for team in ratings.keys():
            if team not in teams_for_ha_opt:
                home_advantages[team] = global_ha
                
        return self.calc_error(events=events,
                              ratings=ratings,
                              home_advantage=home_advantages)
    
    result = minimize(objective,
                     optimiser_advantages,
                     method='L-BFGS-B',
                     bounds=optimiser_bounds,
                     options={'maxiter': max_iterations})
    
    # Update home_advantages with optimized values
    for i, team in enumerate(teams_for_ha_opt):
        home_advantages[team] = result.x[i]
    
    # Return updated home_advantages
    return home_advantages
```

Add a new method for sequential optimization:

```python
def solve_sequential(self, events, ratings, max_iterations=100, 
                    max_cycles=3, convergence_threshold=0.001):
    """
    Sequential optimization approach: optimize ratings and home advantages in alternating cycles
    """
    # Initialize with average home advantage for all teams
    home_advantages = {team: 0.3 for team in ratings.keys()}
    
    # Track error for convergence checking
    previous_error = float('inf')
    current_error = self.calc_error(events, ratings, home_advantages)
    
    cycle = 0
    while cycle < max_cycles and abs(previous_error - current_error) > convergence_threshold:
        # Save previous error for convergence check
        previous_error = current_error
        
        # Step 1: Optimize team ratings with current home advantages
        self.optimise_ratings(events=events,
                             ratings=ratings,
                             home_advantage=home_advantages,
                             max_iterations=max_iterations)
        
        # Step 2: Optimize team-specific home advantages with updated ratings
        home_advantages = self.optimise_team_home_advantages(
            events=events,
            ratings=ratings,
            home_advantages=home_advantages,
            max_iterations=max_iterations
        )
        
        # Check current error
        current_error = self.calc_error(events, ratings, home_advantages)
        cycle += 1
    
    return {
        "ratings": {k: float(v) for k, v in ratings.items()},
        "home_advantages": {k: float(v) for k, v in home_advantages.items()},
        "avg_home_advantage": float(sum(home_advantages.values()) / len(home_advantages)),
        "error": float(current_error),
        "cycles": cycle
    }
```

Extend the existing `solve` method with an option for team-specific home advantages:

```python
def solve(self, events, ratings, home_advantage=None, max_iterations=100, 
         team_specific_ha=False):
    if team_specific_ha:
        return self.solve_sequential(events, ratings, max_iterations)
    else:
        # Original solve method implementation (unchanged)
        if home_advantage:
            self.optimise_ratings(events=events,
                                 ratings=ratings,
                                 home_advantage=home_advantage,
                                 max_iterations=max_iterations)
        else:
            home_advantage = self.optimise_ratings_and_bias(events=events,
                                                          ratings=ratings,
                                                          max_iterations=max_iterations)
        error = self.calc_error(events=events,
                               ratings=ratings,
                               home_advantage=home_advantage)
        return {"ratings": {k: float(v) for k, v in ratings.items()},
                "home_advantage": float(home_advantage),
                "error": float(error)}
```

### 3. Update `main.py` to Support Team-Specific Home Advantages

The `main.py` file will need modifications to handle team-specific home advantages. Specific changes will depend on its current implementation but should include:

- Updating any functions that use home_advantage to handle dictionary inputs
- Adding support for team-specific home advantages in high-level functions
- Ensuring any training functions pass the team_specific_ha parameter to the solver

### 4. Testing and Validation

1. **Unit Tests**: Create tests to verify individual components with team-specific home advantages
2. **Integration Tests**: Test the end-to-end workflow with team-specific home advantages
3. **Comparative Evaluation**: Compare model performance between:
   - Original multiplicative global home advantage
   - Additive global home advantage
   - Team-specific additive home advantages

Focus on:
- Predictive accuracy
- Optimization stability
- Parameter reasonableness checks

### 5. Fallback Mechanisms

Implement fallbacks for edge cases:
- New teams: Use league average home advantage
- Teams with limited data: Use a weighted average between team-specific and league average
- Unreasonable estimates: Constrain extreme values toward the league average

## Technical Considerations

### 1. Optimization Strategy

The proposed implementation uses a **sequential optimization strategy**:
1. Optimize team ratings with current home advantages
2. Optimize team-specific home advantages with updated team ratings
3. Repeat until convergence or maximum cycles reached

This approach was chosen over parallel optimization (optimizing all parameters at once) because:
- Reduces parameter space for each optimization step
- Less prone to overfitting
- More computationally efficient
- Provides more direct control over each parameter type
- Easier to implement constraints for each parameter set

### 2. Constraints and Regularization

The implementation includes several safeguards:
- Home advantage parameters are bounded (typically 0.0 to 0.5 goals)
- Teams with insufficient data fall back to the league average
- Sequential optimization provides implicit regularization
- Convergence criteria prevents unnecessary optimization cycles

### 3. Data Requirements

To estimate reliable team-specific home advantages:
- Each team should have at least 5 home matches in the training dataset
- Consider weighted averaging for teams with limited data

## Benefits

1. **More Accurate Modeling**: Accounts for team-specific home/away performance variations
2. **Better Predictive Power**: Should improve predictions, especially for teams with atypical home advantages
3. **More Granular Insights**: Provides analysis of which teams perform better/worse at home
4. **Fairer Ratings**: Separates team quality from home advantage effects

## Potential Challenges

1. **Data Requirements**: Needs sufficient home matches per team for reliable estimation
2. **Optimization Complexity**: More parameters to optimize, requires careful implementation
3. **Overfitting Risk**: Need to balance model complexity with data availability
4. **Computational Cost**: Sequential optimization will be more computationally intensive

## Implementation Roadmap

1. Implement and test changes to `kernel.py`
2. Implement and test changes to `solver.py`
3. Update `main.py` and other dependent modules
4. Create comprehensive tests and validation procedures
5. Benchmark against existing implementation
6. Document changes and new parameters