
import pandas as pd
import time

file_path = "data.csv"

male_data = pd.read_csv(file_path, delimiter=",")

for index,row in male_data.iterrows():
    time.sleep(0.2)
    if row['Year'] > 1980:
        print(row['Year'], row['Time'])
