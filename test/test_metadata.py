import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.max_row', None)

df = pd.read_csv("../data/metadata/metadata_20251013.csv")
print(df.head(100))
print(df.shape)
print(df.info())