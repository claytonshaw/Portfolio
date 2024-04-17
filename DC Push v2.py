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

    # Getting IDC On Hand
    idc_6060_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6060])
    idc_6061_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6061])
    idc_6088_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6088])
    idc_7042_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7042])
    idc_7067_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7067])
    idc_7078_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7078])
    idc_8980_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6060])

    idc_oh = {6060:idc_6060_oh,6061:idc_6061_oh,6088:idc_6088_oh,7042:idc_7042_oh,7067:idc_7067_oh,7078:idc_7078_oh,8980:idc_8980_oh}

    # Getting DC On Hand
    dc_6021_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6021])
    dc_6026_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6026])
    dc_6031_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6031])
    dc_6037_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6037])
    dc_7026_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7026])
    dc_7033_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7033])
    dc_6010_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6010])
    dc_6020_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6020])
    dc_6054_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6054])
    dc_7035_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7035])
    dc_7038_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7038])
    dc_6023_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6023])
    dc_6027_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6027])
    dc_6030_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6030])
    dc_6038_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6038])
    dc_6080_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6080])
    dc_7034_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7034])
    dc_6012_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6012])
    dc_6016_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6016])
    dc_6019_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6019])
    dc_6035_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6035])
    dc_6036_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6036])
    dc_6068_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6068])
    dc_6094_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6094])
    dc_7036_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7036])
    dc_6006_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6006])
    dc_6011_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6011])
    dc_6017_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6017])
    dc_6018_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6018])
    dc_6048_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6048])
    dc_6066_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6066])
    dc_6069_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6069])
    dc_6009_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6009])
    dc_6025_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6025])
    dc_6043_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6043])
    dc_6092_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6092])
    dc_7039_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7039])
    dc_6024_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6024])
    dc_6039_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6039])
    dc_6040_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6040])
    dc_6070_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6070])
    dc_7045_oh = sum(df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7045])

    dc_oh = {6021:dc_6021_oh, 6026:dc_6026_oh, 6031:dc_6031_oh, 6037:dc_6037_oh, 7026:dc_7026_oh, 7033:dc_7033_oh, 6010:dc_6010_oh, 6020:dc_6020_oh,
            6054:dc_6054_oh, 7035:dc_7035_oh, 7038:dc_7038_oh, 6023:dc_6023_oh, 6027:dc_6027_oh, 6030:dc_6030_oh, 6038:dc_6038_oh, 6080:dc_6080_oh,
            7034:dc_7034_oh, 6012:dc_6012_oh, 6016:dc_6016_oh, 6019:dc_6019_oh, 6035:dc_6035_oh, 6036:dc_6036_oh, 6068:dc_6068_oh, 6094:dc_6094_oh,
            7036:dc_7036_oh, 6006:dc_6006_oh, 6011:dc_6011_oh, 6017:dc_6017_oh, 6018:dc_6018_oh, 6048:dc_6048_oh, 6066:dc_6066_oh, 6069:dc_6069_oh,
            6009:dc_6009_oh, 6025:dc_6025_oh, 6043:dc_6043_oh, 6092:dc_6092_oh, 7039:dc_7039_oh, 6024:dc_6024_oh, 6039:dc_6039_oh, 6040:dc_6040_oh,
            6070:dc_6070_oh, 7045:dc_7045_oh}

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
