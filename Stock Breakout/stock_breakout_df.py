from functions import breakout_profitability, saveResults
from yahoo_fin import stock_info as si
import pandas as pd

# gather stock symbols from major US exchanges
df1 = pd.DataFrame(si.tickers_sp500())
df2 = pd.DataFrame(si.tickers_nasdaq())
df3 = pd.DataFrame(si.tickers_dow())
df4 = pd.DataFrame(si.tickers_other())

# convert DataFrame to list, then to sets
sym1 = set(symbol for symbol in df1[0].values.tolist())
sym2 = set(symbol for symbol in df2[0].values.tolist())
sym3 = set(symbol for symbol in df3[0].values.tolist())
sym4 = set(symbol for symbol in df4[0].values.tolist())

# join the 4 sets into one. Because it's a set, there will be no duplicate symbols
symbols = set.union(sym1, sym2, sym3)
#symbols = set.union(sym1)

# Some stocks are 5 characters. Those stocks with the suffixes listed below are not of interest.
my_list = ['W', 'R', 'P', 'Q']
del_set = set()
sav_set = set()

for symbol in symbols:
    if len( symbol ) > 4 and symbol[-1] in my_list:
        del_set.add( symbol )
    else:
        sav_set.add( symbol )

print( f'Removed {len( del_set )} unqualified stock symbols...' )
print( f'There are {len( sav_set )} qualified stock symbols...' )

results = {}

for stock in sav_set:
    try:
        stock_info = {}
        eb, wr, br, lr, app, anp, ev, tb = breakout_profitability(stock, 1000)
        stock_info['earliest_breakout'] = eb
        stock_info['total_breakouts'] = tb
        stock_info['breakeven_rate'] = f'{br}%'
        stock_info['win_rate'] = f'{wr}%'
        stock_info['loss_rate'] = f'{lr}%'
        stock_info['ave_positive_profit'] = f'{app}%'
        stock_info['ave_negative_profit'] = f'{anp}%'
        stock_info['ev'] = f'{ev}%'

        results[f'Ticker: {stock}'] = stock_info
    except TypeError:
        pass

saveResults(results)
