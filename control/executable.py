
import pandas as pd

file_path = "male100.csv"

male_data = pd.read_csv(file_path, delimiter=",")

for index,row in male_data.iterrows():
    if row['Year'] > 1980:
        print(row['Year'], row['Time'])
