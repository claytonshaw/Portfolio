import pandas as pd
import numpy as np
import openpyxl
import xlsxwriter
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from openpyxl.formula.translate import Translator

df = pd.read_excel(r"C:\Users\clayton\OneDrive - Blackstone Products LLC\Documents\Python Scripts\DC Push\DC Push Build.xlsx" , skiprows=29)

# getting the unique list of SKU's and saving it to a dataframe
unique_sku = df['Vendor Stk Nbr'].unique()

# creating units needed calculation
df['6_wk_fcst'] = df.iloc[:,22:27].sum(axis=1)
df['pipe_minus_fcst'] = df['PIPELINE'] - df['6_wk_fcst']
df['whse_pks_needed'] = df['pipe_minus_fcst'] / df['VNPK Qty']

df['units_needed'] = df.apply(lambda row: 0 if row['whse_pks_needed'] > 0 else row['whse_pks_needed'] * row['VNPK Qty'], axis=1)
df['needed_vnpk_qty'] = df.apply(lambda row: 3 * row['VNPK Qty'] if row["VNPK Qty"] == 1 else row['VNPK Qty'] * 1, axis=1)
df['pipe_need'] = df.apply(lambda row: row['needed_vnpk_qty'] if row['pipe_minus_fcst'] < 0 else row['units_needed'], axis=1)


sto_single = pd.DataFrame()
sto_multi = pd.DataFrame()

for item in unique_sku:
    
    #filtering column to the desired sku and sorting it by pipeline
    df_filtered = df[df['Vendor Stk Nbr'] == item]
    df_filtered = df_filtered.sort_values('PIPELINE',ascending=True).reset_index()

    # Getting IDC On Hand
    idc_6060_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6060]
    idc_6061_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6061]
    idc_6088_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6088]
    idc_7042_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7042]
    idc_7067_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7067]
    idc_7078_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 7078]
    idc_8980_oh = df_filtered['Curr Whse On Hand Qty'][df_filtered['Whse Nbr'] == 6060] 

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


    # calculation for Rolling Sum IC
    df_filtered['units_sent_dc'] = 0
    df_filtered['units_sent_idc'] = 0

    for i in range(len(df_filtered)):
        try:
            if df_filtered['pipe_need'][i] > dc_oh[df_filtered['Whse Nbr'][i]]:
                df_filtered['units_sent_dc'][i] = 0
            elif df_filtered['pipe_need'][i] < dc_oh[df_filtered['Whse Nbr'][i]]:
                df_filtered['units_sent_dc'][i] = df_filtered['pipe_need'][i]
                dc_oh[df_filtered['Whse Nbr'][i]] -= df_filtered['pipe_need'][i]
            elif df_filtered['pipe_need'][i] > idc_oh[df_filtered['IDC'][i]].values:
                df_filtered['units_sent_idc'][i] = 0
            else:
                df_filtered['units_sent_idc'][i] = df_filtered['pipe_need'][i]
                idc_oh[df_filtered['IDC'][i]] -= df_filtered['pipe_need'][i]
        except KeyError:
            pass

    # sorting values by Units Sent to get them to the top
    df_filtered = df_filtered.sort_values(['units_sent_dc','units_sent_idc'],ascending=False)

    # Dropping rows that where the DC's aren't sending anything. 
    condition1 = (df_filtered['units_sent_dc'] == 0) 
    condition2 = (df_filtered['units_sent_idc'] == 0)
    df_filtered = df_filtered[~(condition1 & condition2)]

    # Selecting Columns to Keep
    dc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','Whse Nbr','units_sent_dc']
    idc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','Whse Nbr','units_sent_idc']
    # Select the specified columns and put it into a new DF
    try:
        sto_single = sto_single.append(df_filtered[dc_columns])
    except ValueError:
        pass
    try:
        sto_multi = sto_multi.append(df_filtered[idc_columns])
    except ValueError:
        pass
#dropping rows where the DC's aren't sending anything
sto_single = sto_single.loc[sto_single['units_sent_dc'] != 0]
sto_multi = sto_multi.loc[sto_multi['units_sent_idc'] != 0]

df_filtered.to_excel(r"C:\Users\clayton\OneDrive - Blackstone Products LLC\Documents\Python Scripts\DC Push\DC Push Using Pandas.xlsx")
sto_single.to_excel(r"C:\Users\clayton\OneDrive - Blackstone Products LLC\Documents\Python Scripts\DC Push\sto_single_.xlsx")
sto_multi.to_excel(r"C:\Users\clayton\OneDrive - Blackstone Products LLC\Documents\Python Scripts\DC Push\sto_multi_.xlsx")