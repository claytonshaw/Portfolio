import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime

# Set the page width to a wider value
st.set_page_config(layout="wide")

# Title
st.title("Sales Order and Forecast Dashboard")

# Load data from the CSV file
@st.cache_data
def load_data():
    data = pd.read_csv("Forecast vs SO Quantity Table.csv")
    return data

df = load_data()

# Extract month and year from 'Ship Date'
df['Ship Date'] = pd.to_datetime(df['Ship Date'])
df['Year'] = df['Ship Date'].dt.year
df['Month'] = df['Ship Date'].dt.month

# Filter the data to start from January
filtered_df = df[df['Month'] >= 1]

# Display the filters as dropdowns
st.sidebar.header("Filters")
selected_account_manager = st.sidebar.selectbox("Select Account Manager", ["All"] + list(filtered_df['Account Manager'].unique()))
selected_parent = st.sidebar.selectbox("Select Parent", ["All"] + list(filtered_df['Parent'].unique()))

# Sort and display the 'Item' filter in ascending order
item_values = list(filtered_df['Item'].unique())
item_values.sort()  # Sort the item values
selected_item = st.sidebar.selectbox("Select Item", ["All"] + item_values)

# Apply filters to the data
filtered_data = filtered_df.copy()

if selected_account_manager != "All":
    filtered_data = filtered_data[filtered_data['Account Manager'] == selected_account_manager]

if selected_parent != "All":
    filtered_data = filtered_data[filtered_data['Parent'] == selected_parent]

if selected_item != "All":
    filtered_data = filtered_data[filtered_data['Item'] == selected_item]

# Sum the 'Forecast Qty' and 'SO Quantity' by month
summed_df = filtered_data.groupby(['Year', 'Month']).agg({'Forecast Qty': 'sum', 'SO Quantity': 'sum'}).reset_index()

# Calculate total SO Quantity and Total Forecast Qty
total_so_quantity = int(filtered_data['SO Quantity'].sum())
total_forecast_qty = int(filtered_data['Forecast Qty'].sum())

# Format total numbers with commas
total_so_quantity_formatted = '{:,}'.format(total_so_quantity)
total_forecast_qty_formatted = '{:,}'.format(total_forecast_qty)

# Calculate the forecast variance as (Total Forecast Qty - Total SO Quantity) / Total SO Quantity
forecast_variance = (total_forecast_qty - total_so_quantity) / total_so_quantity

# Format forecast variance as a percentage
forecast_variance_formatted = f'{forecast_variance:.2%}'

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

# Display the total boxes with values and labels
total_col1, total_col2, total_col3 = st.columns(3)
total_col1.markdown(f'<div class="total-box"><div class="total-label">Total SO Quantity</div>{total_so_quantity_formatted}</div>', unsafe_allow_html=True)
total_col2.markdown(f'<div class="total-box"><div class="total-label">Total Forecast Qty</div>{total_forecast_qty_formatted}</div>', unsafe_allow_html=True)
total_col3.markdown(f'<div class="total-box"><div class="total-label">Forecast Variance</div>{forecast_variance_formatted}</div>', unsafe_allow_html=True)

# Display the updated line graph with x-axis as "Month" and y-axis label "Quantity"
fig_updated = px.line(
    summed_df,
    x='Month',
    y=['Forecast Qty', 'SO Quantity'],
    title="Sales Order and Forecast (Updated)",
    labels={'Forecast Qty': 'Total Forecast Qty', 'SO Quantity': 'Total SO Quantity'}
)
fig_updated.update_xaxes(title_text="Month")
fig_updated.update_yaxes(title_text="Quantity")
st.plotly_chart(fig_updated, use_container_width=True)