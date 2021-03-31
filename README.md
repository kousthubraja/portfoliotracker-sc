# portfoliotracker-sc

### APIs for Portfolio Tracker

Hosted at https://rocky-anchorage-39476.herokuapp.com/api/v1/
The hyperlinks are self navigable and Supports REST operations.

#### Example usages:
##### Trades
1. List all trades - GET https://rocky-anchorage-39476.herokuapp.com/api/v1/trade/
2. Add a trade - POST https://rocky-anchorage-39476.herokuapp.com/api/v1/trade/
3. Retrieve a specific trade - GET https://rocky-anchorage-39476.herokuapp.com/api/v1/trade/6/
4. Remove a specific trade - DELETE https://rocky-anchorage-39476.herokuapp.com/api/v1/trade/6/
5. Update a specific trade - PUT https://rocky-anchorage-39476.herokuapp.com/api/v1/trade/6/

##### Portfolio
6. View all positions in a portfolio - GET https://rocky-anchorage-39476.herokuapp.com/api/v1/portfolio/1/
   returns - the returns from the portfolio
