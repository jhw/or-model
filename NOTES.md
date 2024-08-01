### market pricing 01/08/24

- you need to include market pricing here
- because think about include/exclude markets, specifically something like "Without Big Seven"
- you might be tempted to think you can price this by excluding the seven and then normalising the remaining probabilities to one
- but in this case the remaining probabilities sums to something close to zero, so how do you normalise?
- you end up with Aston Villa being 100% because they are the only team outside the top 7 with a chance of winning
- but that's not what's being asked here; in the case where villa collapse, lots of other teams have a chance of beating them
- hence the need to simulate

--- 

- so you really need to be able to pass some kind of mask to SimPoints for the calculation of positions and position probabilities
- or maybe you pass a list of team names
- of maybe you pass include/exclude variables
- then api will have to generate a series of position probability tables
- but it will only return the default one
- the non- defaults will only be used for marks generation
- hence you can pass markets to api which will be priced if you want
- this means the clients can be simplified again
- pricing should be done by a new pricer module

### scipy optimise 21/07/24

- should replace the solver with scipy optimise
- see the variance poisson gist that chatgpt developed [18d0c51199b413a0b8926df7be9cf1ac]
- three passes
  - optimise teams with initial factors guess
  - optimise factors
  - re- optimise teams
