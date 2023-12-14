# Steps
# 1. Download Supplemental Order data from DSS and name in Supplemental Order Data
# 2. Download Available Inventory as a CSV from DOMO and name in "Available Inventory"
# 3. Run script and enjoy the results
# 4. Copy data from sto_single_ file into NOVA sheet

#importing required libraries
import pandas as pd
import numpy as np

# list of parameters
use_custom_vendor_packs = True # switch this to False to use Max Shelf Qty as the cut off
send_to_zero_oh_and_fcst_stores = True # this only changes if using customer vendor packs
vendor_packs_to_send = 1 # number of vendor packs to send to stores
use_available = True # use either on hand or the available inventory

# path to data
file_path = "Supplemental Order Data.xlsx"

# function that will dynamically count the number of blank rows
def blank_rows(file_path):
    # Read the first column of the Excel sheet to find blank rows
    first_column = pd.read_excel(file_path, usecols=[0]).iloc[:, 0]

    # Find the number of consecutive blank rows at the beginning
    blank_rows = 1
    for value in first_column:
        if pd.isnull(value):
            blank_rows += 1
        else:
            break
    return blank_rows

# import necessary files
df = pd.read_excel(file_path, skiprows=blank_rows(file_path))
available_inventory = pd.read_excel(r"Available Inventory.xlsx", skiprows=1) # this dataset gets updated from domo
#available_inventory = pd.read_csv(r"Available Inventory 1.csv") # use this dataset if you want to customize the on hand

# getting the unique list of SKU's and saving it to dataframe
unique_sku = df['Vendor Stk Nbr'].unique()

# creating units needed calculation
df['6_wk_fcst'] = df.iloc[:,16:22].sum(axis=1) # summing each weeks forecast to get a total 6 week forecast
df['pipe_minus_fcst'] = df['PIPELINE'] - df['6_wk_fcst'] # getting pipeline minus forecast
df['pipe_minus_fcst'] = df.apply(lambda row: 0 if row['pipe_minus_fcst'] > 0 else row['pipe_minus_fcst'], axis=1) # if pipeline minus forecast is greater than 0 make it 0
df['pipe_minus_fcst'] = df['pipe_minus_fcst'].abs() # getting absolute value of number
df['whse_pks_needed'] = df['pipe_minus_fcst'] / df['VNPK Qty'] # converting to vendor packs
df['whse_pks_needed'] = df['whse_pks_needed'].apply(np.ceil) # rounding up to the nearest whole number
if use_custom_vendor_packs:
    df['pipe_need'] = df.apply(lambda row: vendor_packs_to_send if row['whse_pks_needed'] > vendor_packs_to_send else row['whse_pks_needed'], axis=1)
    if send_to_zero_oh_and_fcst_stores:
        df['pipe_need'] = df.apply(lambda row: vendor_packs_to_send if (row['6_wk_fcst'] == 0 or row['Curr Str On Hand Qty'] == 0) else row['pipe_need'], axis=1) # if the store's forecast and on hand is zero make the units need max shelf minus pipeline
else:
    df['pipe_need'] = df['whse_pks_needed'] * df['VNPK Qty'] # converting back to units
    df['mx_shelf_minus_pipeline'] = df.apply(lambda row: 0 if row['Max Shelf Qty'] - row['PIPELINE'] < 0 else row['Max Shelf Qty'] - row['PIPELINE'], axis=1) # if max shelf qty minus pipe is les than 0 make it zero other wise make it the difference between max shelf and the pipe
    df['pipe_need'] = df.apply(lambda row: row['Max Shelf Qty'] if row['pipe_need'] > row['Max Shelf Qty'] else row['pipe_need'], axis=1) # if the max shelf qty is less than the needed amount just make it max shelf qty
    df['pipe_need'] = df.apply(lambda row: row['mx_shelf_minus_pipeline'] if (row['6_wk_fcst'] == 0 or row['Curr Str On Hand Qty'] == 0) else row['pipe_need'], axis=1) # if the store's forecast and on hand is zero make the units need max shelf minus pipeline
    df['pipe_need'] = df['pipe_need'] / df['VNPK Qty'] # converting to vendor packs
    df['pipe_need'] = df['pipe_need'].apply(np.ceil) # rounding up to the nearest whole number

#creating an empty dataframe for the loop
sto_single = pd.DataFrame()

for item in unique_sku:
    df_filtered = df[df['Vendor Stk Nbr'] == item]
    df_filtered = df_filtered[df_filtered['Curr Valid Store/Item Comb.'] == 1] # filtering to only valid stores
    df_filtered = df_filtered[df_filtered['Store Type Descr'] != 'BASE STR Nghbrhd Mkt'] # filtering out Neighborhood Market stores
    df_filtered = df_filtered.sort_values('pipe_need', ascending=False).reset_index() # sorting to rank stores with the highest pipe_need

    # getting available inventory 
    blkst_oh = available_inventory[available_inventory['Item'] == item]
    if use_available:
        available_inv = float(blkst_oh.iloc[0][7]) / float(blkst_oh.iloc[0][9]) # uses available - split pack (converts to vendor packs)
    else:
        available_inv = float(blkst_oh.iloc[0][2]) / float(blkst_oh.iloc[0][9]) # uses on hand inventory (converts to vendor packs)

    #reducing available inventory for shared items
    shared_items = [1528,4114,5017,5091,5249,5471]
    if item in shared_items:
        available_inv *= 0.5
    else:
        available_inv

    # zero inventory alert
    if available_inv < 0:
        print(f"{item} has no inventory")

    # calculating rolling sum
    df_filtered['vnpks_sent_dc'] = 0

    for i in range(len(df_filtered)):
        try:
            if df_filtered['pipe_need'][i] > available_inv:
                df_filtered['vnpks_sent_dc'][i] = 0
            elif df_filtered['pipe_need'][i] < available_inv:
                df_filtered['vnpks_sent_dc'][i] = df_filtered['pipe_need'][i]
                available_inv -= df_filtered['pipe_need'][i]
        except KeyError:
            pass

    # sorting the dataframe to put units sent at the top
    df_filtered = df_filtered.sort_values(['vnpks_sent_dc'],ascending=False)

    # Dropping rows that where BLKST isn't sending anything. 
    condition1 = (df_filtered['vnpks_sent_dc'] == 0) 
    df_filtered = df_filtered[~(condition1)]

    # selecting columns to keep
    dc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','vnpks_sent_dc']

    try:
        sto_single = sto_single.append(df_filtered[dc_columns])
    except ValueError:
        pass

    # dropping rows where BLKST isn't sending anything
    sto_single = sto_single.loc[sto_single['vnpks_sent_dc'] != 0]

# exporting data to new files
df_filtered.to_excel(r"Supplemental Order TESTER.xlsx")
sto_single.to_excel(r"sto_single_.xlsx")

# printing total units sent and number of stores by item
sum_by_item = sto_single.groupby('Vendor Stk Nbr')['vnpks_sent_dc'].sum()
store_count_by_item = sto_single.groupby('Vendor Stk Nbr')['vnpks_sent_dc'].count()

result_df = pd.DataFrame({
    'Total VNPK Sent': sum_by_item,
    'Number of Stores': store_count_by_item
})
result_df = result_df.sort_values(by='Total VNPK Sent', ascending=False)
print(result_df)
