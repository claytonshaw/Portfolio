import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from prophet import Prophet
from functions import forecaster


# Set the page width to a wider value
st.set_page_config(layout="wide")

# Title
st.title("SOF Dashboard")

# LOADING DATA
@st.cache_data
def load_data():
    data = pd.read_csv("Forecast vs SO Quantity Table.csv")
    return data

df = load_data()

# DATES AND RANGES
current_year = date.today().year
next_year = current_year + 1
last_year = current_year - 1
today = pd.to_datetime(date.today())
today_last_year = today.replace(year=today.year - 1)
start_of_year = pd.to_datetime(date(today.year, 1, 1))
start_of_last_year = pd.to_datetime(date(today_last_year.year, 1, 1))

# Extract month and year from 'Ship Date'
df['Ship Date'] = pd.to_datetime(df['Ship Date'])
df['Year'] = df['Ship Date'].dt.year
df['Month'] = df['Ship Date'].dt.month



# SIDEBAR
st.sidebar.header("Filters")
selected_account_manager = st.sidebar.selectbox("Select Account Manager", ["All"] + list(sorted(df['Account Manager'].unique())))

# Filter "Parent" options based on the selected "Account Manager"
if selected_account_manager == "All":
    unique_parents = ["All"] + sorted(df['Parent'].unique().tolist())
else:
    unique_parents = ["All"] + sorted(df[df['Account Manager'] == selected_account_manager]['Parent'].unique().tolist())

selected_parent = st.sidebar.selectbox("Select Parent", unique_parents)

# Filter "Item" options based on the selected "Account Manager" and "Parent"
if selected_account_manager == "All" and selected_parent == "All":
    unique_items = ["All"] + sorted(df['Item'].unique().tolist())
elif selected_account_manager == "All":
    unique_items = ["All"] + sorted(df[df['Parent'] == selected_parent]['Item'].unique().tolist())
elif selected_parent == "All":
    unique_items = ["All"] + sorted(df[df['Account Manager'] == selected_account_manager]['Item'].unique().tolist())
else:
    unique_items = ["All"] + sorted(df[(df['Account Manager'] == selected_account_manager) & (df['Parent'] == selected_parent)]['Item'].unique().tolist())

selected_item = st.sidebar.selectbox("Select Item", unique_items)

# Apply filters to the data
filtered_data = df.copy()

if selected_account_manager != "All":
    filtered_data = filtered_data[filtered_data['Account Manager'] == selected_account_manager]

if selected_parent != "All":
    filtered_data = filtered_data[filtered_data['Parent'] == selected_parent]

if selected_item != "All":
    filtered_data = filtered_data[filtered_data['Item'] == selected_item]



# CALCULATIONS FOR KPI'S
# YTD Sales Orders and Forecasts
total_so_qty = int(filtered_data.loc[(filtered_data['Ship Date'] > start_of_year) & (filtered_data['Ship Date'] < today), 'SO Quantity'].sum())
total_forecast_qty = int(filtered_data.loc[(filtered_data['Ship Date'] > start_of_year) & (filtered_data['Ship Date'] < today), 'Forecast Qty'].sum())
total_so_qty_formatted = '{:,}'.format(total_so_qty) # format with commas
total_forecast_qty_formatted = '{:,}'.format(total_forecast_qty) # format with commas

# Forecast Variance
forecast_variance = (total_forecast_qty - total_so_qty) / total_so_qty
forecast_variance_formatted = f'{forecast_variance:.2%}' # format as a percentage

# Calculate SO Quantity growth from this year to last year
last_year_so_qty = int(filtered_data.loc[(filtered_data['Ship Date'] > start_of_last_year) & (filtered_data['Ship Date'] < today_last_year), 'SO Quantity'].sum())
so_qty_growth = (total_so_qty - last_year_so_qty) / last_year_so_qty
so_qty_growth_formatted = f'{so_qty_growth: .2%}' # format as  a percentage

# Creating Prophet Forecast
next_year_prophet = forecaster(filtered_data,next_year)



# CREATING DATAFRAMES 
# Create a new DataFrame for next year's forecast
next_year_forecast_df = filtered_data[filtered_data['Year'] == next_year].groupby(['Year', 'Month']).agg({'Forecast Qty': 'sum'}).reset_index()
next_year_forecast_df['SO Quantity'] = 0  # Set SO Quantity to 0 for next year forecast
next_year_forecast_df.rename(columns = {'Forecast Qty':'Next Year Forecast'}, inplace = True)

# Create a new DataFrame for this year's forecast
this_year_forecast_df = filtered_data[filtered_data['Year'] == current_year].groupby(['Year', 'Month']).agg({'Forecast Qty': 'sum'}).reset_index()
this_year_forecast_df['SO Quantity'] = 0  # Set SO Quantity to 0 for this year forecast
this_year_forecast_df.rename(columns = {'Forecast Qty': 'This Year Forecast'}, inplace = True)

# Create a new DataFrame for this year's SO Quantity
this_year_so_qty_df = filtered_data[filtered_data['Year'] == current_year].groupby(['Year','Month']).agg({'SO Quantity': 'sum'}).reset_index()
this_year_so_qty_df['Forecast Qty'] = 0
this_year_so_qty_df.rename(columns = {'SO Quantity': 'This Year SO Quantity'}, inplace = True)

# Create a new Data Frame for last year's SO Quantity
last_year_so_qty_df = filtered_data[filtered_data['Year'] == last_year].groupby(['Year','Month']).agg({'SO Quantity':'sum'}).reset_index()
last_year_so_qty_df['Forecast Qty'] = 0
last_year_so_qty_df.rename(columns = {'SO Quantity': 'Last Year SO Quantity'}, inplace = True)

# Concatenate the DataFrames for current year, next year, and previous years
combined_df = pd.DataFrame()
combined_df['Month'] = this_year_forecast_df['Month']
combined_df['This Year SO Quantity'] = this_year_so_qty_df['This Year SO Quantity'].astype(int)
combined_df['Last Year SO Quantity'] = last_year_so_qty_df['Last Year SO Quantity'].astype(int)
combined_df['This Year Forecast'] = this_year_forecast_df['This Year Forecast'].astype(int)
combined_df['Next Year Forecast'] = next_year_forecast_df['Next Year Forecast'].astype(int)



# ADDING ELEMENTS TO WEBPAGE
left_column, right_column = st.columns([3,1])   

# create an editable dataframe
combined_df.drop(columns = ['This Year SO Quantity','Last Year SO Quantity','This Year Forecast'], inplace = True)
combined_df_editable = left_column.data_editor(combined_df.T)
combined_df_reposed = combined_df_editable.T.reset_index()

# Calculate Next Year Total Forecast Qty
next_year_total_forecast = int(combined_df_reposed['Next Year Forecast'].sum())
next_year_total_forecast_formatted = '{:,}'.format(next_year_total_forecast)

# Apply CSS for styling the total boxes
st.markdown(
    """
    <style>
    .total-box {
        text-align: center;
        padding: 10px;
        background-color: #f0f0f0;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 24px;
        margin: 10px;
        color: black; /* Change font color to black */
    }
    .total-label {
        font-size: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Instruction Box
new_forecast = right_column.write('Instructions: Select from filters and then try typing a new number in the table.')

st.divider()

# Display the total boxes with values and labels
total_col1, total_col2, total_col3, total_col4, total_col5 = st.columns(5)
total_col1.markdown(f'<div class="total-box"><div class="total-label">SO Quantity</div>{total_so_qty_formatted}</div>', unsafe_allow_html=True)
total_col2.markdown(f'<div class="total-box"><div class="total-label">SO Quantity Growth</div>{so_qty_growth_formatted}</div>', unsafe_allow_html=True)
total_col3.markdown(f'<div class="total-box"><div class="total-label">Forecast Variance</div>{forecast_variance_formatted}</div>', unsafe_allow_html=True)
total_col4.markdown(f'<div class="total-box"><div class="total-label">Total Forecast</div>{total_forecast_qty_formatted}</div>', unsafe_allow_html=True)
total_col5.markdown(f'<div class="total-box"><div class="total-label">Next Year Total Forecast</div>{next_year_total_forecast_formatted}</div>', unsafe_allow_html=True)

# Create the line graph figure
fig_updated = px.line(
    combined_df_reposed,
    x='Month',
    y=['Next Year Forecast'],
    color_discrete_map={'Next Year Forecast':'red'}
)

# Add the lines for "This Year Forecast" and "Next Year Forecast"
fig_updated.add_scatter(x=this_year_forecast_df['Month'], y=this_year_forecast_df['This Year Forecast'], mode='lines', name='This Year Forecast', line=dict(color='#cc5628'))
fig_updated.add_scatter(x=this_year_so_qty_df['Month'], y=this_year_so_qty_df['This Year SO Quantity'], mode='lines', name='This Year SO Quantity', line=dict(color='#2f4359'))
fig_updated.add_scatter(x=last_year_so_qty_df['Month'], y=last_year_so_qty_df['Last Year SO Quantity'], mode='lines', name='Last Year SO Quantity', line=dict(color='#949598'))
fig_updated.add_scatter(x=next_year_prophet['Month'], y=next_year_prophet['yhat'], mode='lines', name='Prophet Forecast', line=dict(color='pink'))

fig_updated.update_xaxes(title_text="Month Number", showgrid=True, dtick=True)
fig_updated.update_yaxes(title_text="Unit Quantity")
fig_updated.update_layout(legend = dict(
    orientation='h',
    yanchor='bottom',
    y=1.07,
    xanchor='right',
    x=0.7),
    legend_title = ''
)

# Display the updated line graph
st.plotly_chart(fig_updated, use_container_width=True)
