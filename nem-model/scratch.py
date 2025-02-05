
import pandas as pd

generators_raw = pd.read_csv('battle-nem/data/generators.csv')
pricelevel_raw = pd.read_csv('battle-nem/data/pricelevel.csv')

generators = list(generators_raw['generator_name'].unique())
price_bands = list(pricelevel_raw['pricelevel'].unique())

# Create all combinations of generators and price bands
combinations = [(gen, price) for gen in generators for price in price_bands]

# Convert to dataframe
bid_frame = pd.DataFrame(combinations, columns=['generator', 'price_band'])

# Write bid frame to CSV
bid_frame.to_csv('battle-nem/data/bid_combinations.csv', index=False)

