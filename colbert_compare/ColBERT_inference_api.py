import requests
import pandas as pd
from tqdm import tqdm
import csv
import math
import glob
import os
import json

        
def request_colbert(url, obs, query):
    data = {
            "obs": obs, 
            "query": query,
            "task_id": 1,
            "k": 50
        }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def filter_page(response, top_k=(1, 5, 10, 50)):
    results = []

    for k in top_k:
        top_k_passages = sorted(response, key=lambda x: x[1], reverse=True)[:k]
        top_k_labels = [passage[0] for passage in top_k_passages]
        results.append((k, top_k_labels))
    
    return results

def update_last_processed_index(index, index_file):
    with open(index_file, 'w') as f:
        f.write(str(index))

def get_last_processed_index(index_file):
    try:
        with open(index_file, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

if __name__ == "__main__":
    df = pd.read_csv("preprocessed_mind2web.csv")
    output_csv = "search_results.csv"
    url = "http://0.0.0.0:5001/search"
    index_file = "last_processed_index.txt"

    last_processed_index = get_last_processed_index(index_file)

    # with open(output_csv, mode='a', newline='', encoding='utf-8') as file:
    #     writer = csv.writer(file)

    #     for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    #         obs = row[1].split('\n')
    #         query = row[0]

    #         if index <= last_processed_index:
    #             continue
        
    #         response = request_colbert(url, obs, query)

    #         if response:
    #             response_data = response.json()
    #             filtered_results = filter_page(response_data["passages"])

    #             row_data = [index, query, obs] + filtered_results
    #             writer.writerow(row_data)
    #         else:
    #             print(f"Error for row {index}")
    #             writer.writerow([index, query, obs] + ['Error'] * 4)  # 'Error' for each k value column
            
    #         update_last_processed_index(index, index_file)


    ## mind2web
    output_file = 'mind2web.txt'
    file_path = 'data/mind2web.csv'
    df = pd.read_csv(file_path)
    val_start_idx =  math.floor(len(df) * 0.8)

    with open(output_file, 'w') as wf:
        for i in tqdm(range(val_start_idx, len(df))):
            ex = df.iloc[len(df)-i-1]
            action_string = ex['ACTION']
            objective = ex['OBJECTIVE']
            wf.write(f'{len(df)-i-1}, Task: {objective}; Action: {action_string}\n')
            results = filter_page(ex['OBSERVATION'], objective)
            for k, top_k_labels in results:
                wf.write(f'k={k}: {top_k_labels}\n')
            wf.write('=' * 50 + '\n')

    ## webarena

    base_dir = 'data/webarena_acc_tree'
    pattern = os.path.join(base_dir, 'render_*_tree_0.txt')
    output_file = 'webarena_results.txt'

    with open('data/webarena_test.json', 'r') as f:
        webarena_data = json.load(f)
        id2objective = {}
        for d in webarena_data:
            id2objective[d['task_id']] = d['intent']

    with open(output_file, 'w') as output:
        for file_path in tqdm(glob.glob(pattern)):
            with open(file_path, 'r') as f:
                html_content = '\n'.join([s for s in f.readlines()])
                # Extracting the task_id from the file name
                task_id = int(file_path.split('/')[-1].split('_')[1])
                objective = id2objective[task_id]

            output.write(f"{task_id} Task: {objective}\n")
            results = filter_page(html_content, objective)
            for k, top_k_labels in results:
                output.write(f"k={k}: {top_k_labels}\n")
            output.write('=' * 50 + '\n')
    
    