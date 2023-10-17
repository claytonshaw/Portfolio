import pandas as pd
import numpy as np
import openpyxl
from openpyxl import load_workbook
from openpyxl.formula import Tokenizer
from openpyxl.formula.translate import Translator

df = pd.read_excel(r"C:\Users\clata\OneDrive\Desktop\python\work\supplemental order\Supplemental Order Data.xlsx", skiprows=24)
available_inventory = pd.read_csv(r"C:\Users\clata\OneDrive\Desktop\python\work\supplemental order\Available Inventory.csv")

# getting the unique list of SKU's and saving it to dataframe
unique_sku = df['Vendor Stk Nbr'].unique()

# creating units needed calculation
df['6_wk_fcst'] = df.iloc[:,16:22].sum(axis=1)
df['pipe_minus_fcst'] = df['PIPELINE'] - df['6_wk_fcst']
df['whse_pks_needed'] = df['pipe_minus_fcst'] / df['VNPK Qty']

df['units_needed'] = df.apply(lambda row: 0 if row['whse_pks_needed'] > 0 else row['whse_pks_needed'] * row['VNPK Qty'], axis=1)
df['needed_vnpk_qty'] = df.apply(lambda row: 3 * row['VNPK Qty'] if row["VNPK Qty"] == 1 else row['VNPK Qty'] * 1, axis=1)
df['pipe_need'] = df.apply(lambda row: row['needed_vnpk_qty'] if row['pipe_minus_fcst'] < 0 else row['units_needed'], axis=1)


sto_single = pd.DataFrame()

for item in unique_sku:
    df_filtered = df[df['Vendor Stk Nbr'] == item]
    df_filtered = df_filtered.sort_values('PIPELINE', ascending=True).reset_index()

    # getting available inventory 
    inv_item = item
    item_string = str(inv_item)
    available_inventory[available_inventory['Item'] == item_string]
    available_inv = available_inventory.iloc[0][2]

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


df.to_excel(r"C:\Users\clata\OneDrive\Desktop\python\work\supplemental order\Supplemental Order TESTER.xlsx")
sto_single.to_excel(r"C:\Users\clata\OneDrive\Desktop\python\work\supplemental order\sto_single_.xlsx")
