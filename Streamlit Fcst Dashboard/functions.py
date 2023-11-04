import pandas as pd
import plotly.express as px
from datetime import date, datetime
from prophet import Prophet

#creating forecaster function 
def forecaster(data, next_year):
    forecast_df = data.groupby(['Ship Date']).agg({'SO Quantity': 'sum'}).reset_index()
    forecast_df = forecast_df[forecast_df['Ship Date'] <= pd.to_datetime(date.today())]
    forecast_df = forecast_df.rename(columns={'Ship Date': 'ds', 'SO Quantity': 'y'})  # Rename columns to 'ds' and 'y'
    m = Prophet()
    m.fit(forecast_df)
    future = m.make_future_dataframe(periods=365)
    forecast = m.predict(future)
    forecast.rename(columns = {'ds':'Ship Date'}, inplace = True)
    forecast['Year'] = forecast['Ship Date'].dt.year
    forecast['Month'] = forecast['Ship Date'].dt.month
    next_year_prophet = forecast[forecast['Year']==next_year].groupby(['Year','Month']).agg({'yhat':'sum'}).reset_index().astype(int)
    
    return next_year_prophet
