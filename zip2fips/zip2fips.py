import pandas as pd
import json

# Load JSON file
with open('zip2fips.json') as f:
    json_data = json.load(f)

# Create a DataFrame
df = pd.DataFrame([(zip_code, fips_code) for zip_code, fips_codes in json_data.items() for fips_code in fips_codes],
                  columns=['Zip Code', 'FIPS Code'])

# Write the modified DataFrame to CSV
df.to_csv('zip2fips.csv', index=False)
