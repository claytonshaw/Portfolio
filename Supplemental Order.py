# Steps
# 1. Download Supplemental Order data from DSS and name in Supplemental Order Data
# 2. Download Available Inventory as a CSV from DOMO and name in "Available Inventory"
# 3. Run script and enjoy the results
# 4. Copy data from sto_single_ file into NOVA sheet

#importing required libraries
import pandas as pd
import numpy as np
import openpyxl
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from openpyxl.formula.translate import Translator

# import necessary files
df = pd.read_excel(r"Supplemental Order Data.xlsx", skiprows=24)
available_inventory = pd.read_csv(r"Available Inventory.csv")

# getting the unique list of SKU's and saving it to dataframe
unique_sku = df['Vendor Stk Nbr'].unique()

# creating units needed calculation
df['6_wk_fcst'] = df.iloc[:,16:22].sum(axis=1)
df['pipe_minus_fcst'] = df['PIPELINE'] - df['6_wk_fcst']
df['pipe_minus_fcst'] = df.apply(lambda row: 0 if row['pipe_minus_fcst'] > 0 else row['pipe_minus_fcst'], axis=1)
df['pipe_minus_fcst'] = df['pipe_minus_fcst'].abs()
df['whse_pks_needed'] = df['pipe_minus_fcst'] / df['VNPK Qty']
df['whse_pks_needed'] = df['whse_pks_needed'].apply(np.ceil)
df['pipe_need'] = df['whse_pks_needed'] * df['VNPK Qty']
df['pipe_need'] = df.apply(lambda row: row['Max Shelf Qty'] if row['pipe_need'] > row['Max Shelf Qty'] else row['pipe_need'], axis=1)

sto_single = pd.DataFrame()

for item in unique_sku:
    df_filtered = df[df['Vendor Stk Nbr'] == item]
    df_filtered = df_filtered[df_filtered['Curr Valid Store/Item Comb.'] == 1]
    df_filtered = df_filtered[df_filtered['Store Type Descr'] != 'BASE STR Nghbrhd Mkt']
    df_filtered = df_filtered.sort_values('pipe_need', ascending=False).reset_index()

    # getting available inventory 
    blkst_oh = available_inventory[available_inventory['Item'] == str(item)]
    available_inv = blkst_oh.iloc[0][2]

    #reducing available inventory for shared items
    shared_items = [1528,4114,5017,5091,5249,5471]
    if item in shared_items:
        available_inv *= 0.5
    else:
        available_inv

    # calculating rolling sum
    df_filtered['units_sent_dc'] = 0

    for i in range(len(df_filtered)):
        try:
            if df_filtered['pipe_need'][i] > available_inv:
                df_filtered['units_sent_dc'][i] = 0
            elif df_filtered['pipe_need'][i] < available_inv:
                df_filtered['units_sent_dc'][i] = df_filtered['pipe_need'][i]
                available_inv -= df_filtered['pipe_need'][i]
        except KeyError:
            pass

    # sorting the dataframe to put units sent at the top
    df_filtered = df_filtered.sort_values(['units_sent_dc'],ascending=False)

    # Dropping rows that where BLKST isn't sending anything. 
    condition1 = (df_filtered['units_sent_dc'] == 0) 
    df_filtered = df_filtered[~(condition1)]

    # selecting columns to keep
    dc_columns = ['Prime Item Nbr', 'Vendor Stk Nbr','Store Nbr','units_sent_dc']

    try:
        sto_single = sto_single.append(df_filtered[dc_columns])
    except ValueError:
        pass
    
    # dropping rows where BLKST isn't sending anything
    sto_single = sto_single.loc[sto_single['units_sent_dc'] != 0]

# exporting data to new files
df_filtered.to_excel(r"Supplemental Order TESTER.xlsx")
sto_single.to_excel(r"sto_single_.xlsx")
