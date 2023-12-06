import math
import pandas as pd
from tqdm import tqdm
import csv
from colbert_compare.ColBERT_inference_api import request_colbert


file_path = 'data/mind2web.csv'
output_csv = 'results.csv'

df = pd.read_csv(file_path)

val_start_idx = math.floor(len(df) * 0.8)

# Open the output CSV file in append mode
with open(output_csv, mode='a', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)

    # Iterate over each row in the DataFrame from val_start_idx to end
    for index, row in tqdm(enumerate(df.iloc[val_start_idx:].itertuples()), total=len(df) - val_start_idx):
        obs = row.OBSERVATION.split('\n')
        query = row.ACTION

        # Assuming request_colbert makes the necessary request and returns the response
        response = request_colbert(obs, query, index)

        # Check if the request was successful and write to CSV
        if response.status_code == 200:
            writer.writerow([index, query, obs, response.json()])
            print(f"Search Results for row {index} written to CSV")
        else:
            print(f"Error for row {index}:", response.text)
            writer.writerow([index, query, obs, "Error"])
