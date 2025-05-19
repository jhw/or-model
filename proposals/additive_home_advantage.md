# Additive Home Advantage Implementation Proposal

## Background

Currently, the or-model implements home advantage as a multiplicative factor applied to the home team's rating:

```python
home_lambda = ratings[home_team_name] * home_advantage
```

This means stronger teams (with higher ratings) receive a larger absolute boost when playing at home than weaker teams.

## Proposed Change

Change the home advantage implementation from a multiplicative factor to an additive fixed goal value. This would give all teams the same absolute boost in expected goals when playing at home, regardless of team strength.

## Implementation Plan

### 1. Modify `kernel.py`

Update the `ScoreMatrix.initialise` method to use addition instead of multiplication:

```python
@classmethod
def initialise(self, event_name, ratings, home_advantage, n = 11, rho = 0.1):
    home_team_name, away_team_name = event_name.split(" vs ")
    # Change from multiplicative to additive
    home_lambda = ratings[home_team_name] + home_advantage
    away_lambda = ratings[away_team_name]
    return ScoreMatrix(home_lambda, away_lambda, n, rho)
```

### 2. Update `solver.py`

Modify the home advantage constraint range to be appropriate for an additive model:

```python
# Change from (1, 1.5) to a range appropriate for goal differences
HomeAdvantageRange = (0, 0.5)  # Reasonable range for additional goals
```

### 3. Run Tests

Ensure all tests pass with the new implementation. The interpretation of the home advantage parameter has changed, so some test values may need adjustment.

### 4. Re-optimize Model Parameters

Re-run optimization with the new additive model to find appropriate team ratings and home advantage values:

```python
# Example code to re-optimize parameters
from model.main import train

# Load historical match data
historical_data = load_data(...)

# Re-train model with new additive home advantage implementation
results = train(historical_data)
```

### 5. Evaluate Model Performance

Compare the prediction accuracy of the new additive model against the old multiplicative model:

1. Run both models against a test dataset
2. Compare RMSE, log loss, or other relevant metrics
3. Analyze if the additive model changes predictions significantly

### 6. Documentation Updates

Update documentation to reflect the new interpretation of the home advantage parameter:

- Old: "home_advantage = 1.2" means "home teams score 20% more goals"
- New: "home_advantage = 0.3" means "home teams score 0.3 more goals"

## Considerations

1. **Model Interpretation**: The additive approach makes the home advantage parameter more intuitive (directly interpretable as additional expected goals).

2. **Team Strength Interaction**: 
   - Old model: stronger teams received a larger absolute boost
   - New model: all teams receive the same absolute boost

3. **Parameter Scale**: 
   - Home advantage will now be measured in goals rather than as a multiplier
   - Typical values will likely be in the 0.2-0.4 range instead of 1.1-1.3 range

4. **Potential Further Enhancements**:
   - This change could easily lead into team-specific home advantages
   - Could explore time-based decay of home advantage