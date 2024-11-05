import pandas as pd
import numpy as np

# list of parameters (RUN THROUGH THESE BEFORE YOU RUN THROUG THE REPORT)
use_custom_vendor_packs = False # switch this to False to use Max Shelf Qty as the cut off
vendor_packs_to_send = 1 # number of vendor packs to send to stores
sort_by_zero_oh = True # if true we will target stores that have zero on hand first

# path to data
file_path = "DC Push Data.xlsx"

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

df = pd.read_excel(file_path, skiprows=blank_rows(file_path))

# getting the unique list of SKU's and saving it to a dataframe
unique_sku = df['Vendor Stk Nbr'].unique()

# creating units needed calculation
df['6_wk_fcst'] = df.iloc[:,22:27].sum(axis=1) # adding up the 6 week forecast
df['pipe_minus_fcst'] = df['PIPELINE'] - df['6_wk_fcst'] # getting pipeline minus forecast
df['pipe_minus_fcst'] = df.apply(lambda row: 0 if row['pipe_minus_fcst'] > 0 else row['pipe_minus_fcst'], axis=1) # if pipeline minus forecast is greater than 0 make it 0
df['pipe_minus_fcst'] = df['pipe_minus_fcst'].abs() # getting absolute value of number
df['whse_pks_needed'] = df['pipe_minus_fcst'] / df['VNPK Qty'] # converting to vendor packs
df['whse_pks_needed'] = df['whse_pks_needed'].apply(np.ceil) # rounding up to the nearest whole number
if use_custom_vendor_packs:
    df['pipe_need'] = df.apply(lambda row: vendor_packs_to_send if row['whse_pks_needed'] > vendor_packs_to_send else row['whse_pks_needed'], axis=1)
    df['pipe_need'] = df.apply(lambda row: vendor_packs_to_send if (row['6_wk_fcst'] == 0 and row['Curr Str On Hand Qty'] == 0) else row['pipe_need'], axis=1) # if the store's forecast and on hand is zero make the units need max shelf minus pipeline
else:
    df['pipe_need'] = df['whse_pks_needed'] * df['VNPK Qty'] # converting back to units
    df['mx_shelf_minus_pipeline'] = df.apply(lambda row: 0 if row['Max Shelf Qty'] - row['PIPELINE'] < 0 else row['Max Shelf Qty'] - row['PIPELINE'], axis=1) # if max shelf qty minus pipe is les than 0 make it zero other wise make it the difference between max shelf and the pipe
    df['pipe_need'] = df.apply(lambda row: row['Max Shelf Qty'] if row['pipe_need'] > row['Max Shelf Qty'] else row['pipe_need'], axis=1) # if the max shelf qty is less than the needed amount just make it max shelf qty
    df['pipe_need'] = df.apply(lambda row: row['mx_shelf_minus_pipeline'] if (row['6_wk_fcst'] == 0 and row['Curr Str On Hand Qty'] == 0) else row['pipe_need'], axis=1) # if the store's forecast and on hand is zero make the units need max shelf minus pipeline
    df['pipe_need'] = df['pipe_need'] / df['VNPK Qty'] # converting to vendor packs
    df['pipe_need'] = df['pipe_need'].apply(np.ceil) # rounding up to the nearest whole number


sto_single = pd.DataFrame()
sto_multi = pd.DataFrame()

for item in unique_sku: 
    #filtering column to the desired sku and sorting it by pipeline
    df_filtered = df[df['Vendor Stk Nbr'] == item]
    df_filtered = df_filtered[df_filtered['Store Type Descr'] != 'BASE STR Nghbrhd Mkt'] # filtering out Neighborhood Market stores
    if sort_by_zero_oh:
        df_filtered = df_filtered.sort_values(by = ['Curr Str On Hand Qty', 'pipe_need'], ascending=[False, False]).reset_index() # sort by stores that have zero on hand and pipe need
    else:
        df_filtered = df_filtered.sort_values('pipe_need', ascending=False).reset_index() # sorting to rank stores with the highest pipe_need

    # List of distribution center numbers
    idc_numbers = [6060, 6061, 6088, 7042, 7067, 7078, 8980]

    # Dictionary comprehension to calculate the sum for each distribution center
    idc_oh = {dc: sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == dc])
                for idc in idc_numbers}

    # List of distribution center numbers
    dc_numbers = [6021, 6026, 6031, 6037, 7026, 7033, 6010, 6020, 6054, 7035, 7038, 6023, 6027, 6030, 6038, 
                6080, 7034, 6012, 6016, 6019, 6035, 6036, 6068, 6094, 7036, 6006, 6011, 6017, 6018, 6048, 
                6066, 6069, 6009, 6025, 6043, 6092, 7039, 6024, 6039, 6040, 6070, 7045]

    # Dictionary comprehension to calculate the sum for each distribution center
    dc_oh = {dc: sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == dc]) for dc in dc_numbers}

    df_filtered = df_filtered[df_filtered['Curr Valid Store/Item Comb.'] == 1] # filtering to only valid stores

    # calculation for Rolling Sum IC
    df_filtered['vnpks_sent_dc'] = 0
    df_filtered['vnpks_sent_idc'] = 0

    for i in range(len(df_filtered)):
        try:
            if (df_filtered['pipe_need'][i] > dc_oh[df_filtered['Whse Nbr'][i]]) & (df_filtered['pipe_need'][i] > idc_oh[df_filtered['IDC'][i]]):
                df_filtered['vnpks_sent_dc'][i] = 0
            elif df_filtered['pipe_need'][i] < dc_oh[df_filtered['Whse Nbr'][i]]:
                df_filtered['vnpks_sent_dc'][i] = df_filtered['pipe_need'][i]
                dc_oh[df_filtered['Whse Nbr'][i]] -= df_filtered['pipe_need'][i]
            else:
                df_filtered['vnpks_sent_idc'][i] = df_filtered['pipe_need'][i]
                idc_oh[df_filtered['IDC'][i]] -= df_filtered['pipe_need'][i]
        except KeyError:
            pass

    # sorting values by Units Sent to get them to the top
    df_filtered = df_filtered.sort_values(['vnpks_sent_dc','vnpks_sent_idc'],ascending=False)

    # Dropping rows that where the DC's aren't sending anything. 
    condition1 = (df_filtered['vnpks_sent_dc'] == 0) 
    condition2 = (df_filtered['vnpks_sent_idc'] == 0)
    df_filtered = df_filtered[~(condition1 & condition2)]

    # Selecting Columns to Keep
    dc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','Whse Nbr','vnpks_sent_dc']
    idc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','IDC','vnpks_sent_idc']
    # Select the specified columns and put it into a new DF
    try:
        sto_single = sto_single.append(df_filtered[dc_columns])
    except ValueError:
        pass
    try:
        sto_multi = sto_multi.append(df_filtered[idc_columns])
    except ValueError:
        pass

###### END OF THE FOR LOOP

#dropping rows where the DC's aren't sending anything
sto_single = sto_single.loc[sto_single['vnpks_sent_dc'] != 0]
sto_multi = sto_multi.loc[sto_multi['vnpks_sent_idc'] != 0]

df_filtered.to_excel('DC Push TESTER.xlsx')
sto_single.to_excel('sto_single_.xlsx')
sto_multi.to_excel('sto_multi_.xlsx')
