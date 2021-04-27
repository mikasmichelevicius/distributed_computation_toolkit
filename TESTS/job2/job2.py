
import pandas as pd
import time

# Job example that uses an external data file called data.csv
# It will filter and print some attributes of the dataset
# as specified below. The system will return successfully 
# completed job containing the filtered data in the stdout
# file upon job completion.

file_path = "data.csv"

male_data = pd.read_csv(file_path, delimiter=",")

for index,row in male_data.iterrows():
    time.sleep(1)
    if row['Year'] > 1980:
        print(row['Year'], row['Time'])
