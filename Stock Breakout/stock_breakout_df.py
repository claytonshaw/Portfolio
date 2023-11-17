from functions import breakout_profitability

sp500_top_stocks = [
    'TSLA',
    'AMZN',
    'ZM',
    'NIO',
    'PLTR'
]
for i in sp500_top_stocks:
    breakout_profitability(i)