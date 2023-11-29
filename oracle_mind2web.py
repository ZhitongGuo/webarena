'''

query	obs	action	windowed_obs	bounded_obs	compression_rate_adj	compression_rate_bound	correct_count_adj	correct_count_bound

plan: 
1. find action element in obs
2. append the element in the obs
3. query with gpt, ask for the next action, see if it can actually predict it
4. query template: 
"OBSERVATION:{observation}PREVIOUS ACTIONS:{}"

       
'''

import csv
import re
import openai  
import pandas as pd
from tqdm import tqdm
import json
import os

instruction_path = "/home/zhitongg/webarena/mind2web_p_cot_id_actree_2s_no_na.json"

def save_last_processed_index(index):
    with open("oracle_last_processed_index.txt", "w") as f:
        f.write(str(index))

def load_last_processed_index():
    try:
        with open("oracle_last_processed_index.txt", "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

def save_error_index(index):
    with open("oracle_error.txt", "a") as f:
        f.write(str(index)+"\n")

def testing():
    last_processed_index = load_last_processed_index()
    mode = 'a' if last_processed_index > 0 else 'w'
    mind2web_data = pd.read_csv("/home/zhitongg/webarena/ColBERT/preprocessed_mind2web.csv")

    

    with open(f"oracle_mind2web.csv", mode=mode, newline='') as file2:
        
        writer = csv.writer(file2)
        if last_processed_index == 0:
            writer.writerow(['query', 'obs', 'action', 'prev_action', 'windowed_obs', 'contained', 'modified_obs', 'predict_action', 'success'])
    
        for i, data in tqdm(enumerate(mind2web_data.iterrows()), total=mind2web_data.shape[0]):
            index, row = data
            if index <= last_processed_index:
                continue

            action_element = extract_element_number(row['action'])
            success = 0
            if action_element:
                contained, modified_obs = append_element_to_obs(row['obs'], row['windowed_obs'], action_element)
                try:
                    next_action_prediction = predict_next_action(row['query'], row['PREVIOUS ACTIONS'], modified_obs)
                except:
                    save_error_index(index)
                    writer.writerow([row['query'], row['obs'],  row['action'],row['PREVIOUS ACTIONS'], row['windowed_obs'],contained, modified_obs, -1, -1])
                    continue
                next_action_num = extract_element_number(next_action_prediction)
                if next_action_num == action_element:
                    success = 1
            writer.writerow([row['query'], row['obs'],  row['action'],row['PREVIOUS ACTIONS'], row['windowed_obs'],contained, modified_obs, next_action_prediction, success])
            file2.flush()

            save_last_processed_index(index)
                    
                
def predict_next_action(intent, previous_action_str, obs, mode = 'chat'):
    instruction = json.load(open(instruction_path))
    instruction["examples"] = [tuple(e) for e in instruction["examples"]]
    intro = instruction["intro"]
    examples = instruction["examples"]
    template = instruction["template"]
    keywords = instruction["meta_data"]["keywords"]

    current = template.format(
            objective=intent,
            observation=obs,
            previous_action=previous_action_str,
        )
    openai.api_key = os.environ["OPENAI_API_KEY"]
    openai.organization = os.environ.get("OPENAI_ORGANIZATION", "")

    if mode == "chat":
        message = [{"role": "system", "content": intro}]
        for (x, y) in examples:
            message.append(
                {
                    "role": "system",
                    "name": "example_user",
                    "content": x,
                }
            )
            message.append(
                {
                    "role": "system",
                    "name": "example_assistant",
                    "content": y,
                }
            )
        message.append({"role": "user", "content": current})

        response = openai.ChatCompletion.create(  # type: ignore
            model="gpt-3.5-turbo-0613",
            messages=message,
            temperature=1.0,
            max_tokens=384,
            top_p=0.9,
            stop=None,
        )
    elif mode == "completion":
        message = f"{intro}\n\n"
        message += "Here are a few examples:\n"
        for example in examples:
            message += f"Observation\n:{example[0]}\n\n"
            message += f"Action: {example[1]}\n\n"
        message += "Now make prediction given the observation\n\n"
        message += f"Observation\n:{current}\n\n"
        message += "Action:"

        response = openai.Completion.create(  # type: ignore
            model="gpt-3.5-turbo",
            prompt=message,
            temperature=1.0,
            max_tokens=384,
            top_p=0.9,
            stop=None,
        )

    return response.choices[0].message.content

def extract_element_number(action_str):
    """Extracts the element number from the action string."""
    match = re.search(r'\[(\d+)\]', action_str)
    return match.group(1) if match else None

def append_element_to_obs(obs, windowed_obs, element_number):
    """Appends the element description to the observation based on the element number."""
    if f'[{element_number}]' in windowed_obs:
        return 1, windowed_obs

    true_index = 0
    for element in obs.split('\n'):
        if element in windowed_obs:
            true_index += 1
        if f'[{element_number}]' in element:
            true_element = element
            break
    windowed_list = windowed_obs.split('\n')
    windowed_list.insert(true_index+1, true_element)
    windowed_obs = '\n'.join(windowed_list)
    return 0, windowed_obs


testing()

# def predict_next_action(prev_action, modified_obs):
#     """Queries GPT for the next action prediction."""
#     # Construct your query here
#     query = f"Previous action: {prev_action}\nOBSERVATION: {modified_obs}\nWhat is the next action?"
#     # Send the query to GPT and get the response (this part depends on your specific GPT setup)
#     response = openai.Completion.create(prompt=query, ...)  # Fill in the appropriate parameters
#     return response.choices[0].text.strip() if response.choices else "No prediction"

# def get_gpt3_5_response(prompt, current, api_key, max_tokens=2048):
#     message = [{"role": "system", "content": prompt["intro"]}]
#     for (x, y) in prompt["examples"]:
#         message.append(
#             {
#                 "role": "system",
#                 "name": "example_user",
#                 "content": x,
#             }
#         )
#         message.append(
#             {
#                 "role": "system",
#                 "name": "example_assistant",
#                 "content": y,
#             }
#         )
#     message.append({"role": "user", "content": current})
#     response = openai.ChatCompletion.create(
#       model="gpt-3.5-turbo",  # Specify the model here
#       messages=message,
#       temperature=1.0,
#       top_p=0.9,
#       # context_length=0,
#       max_tokens=384,
#       # stop_token=None,
#     )

#     print(response.choices[0].message.content)
#     return response.choices[0].message.content






# def get_windowed_obs(obs, query, indexer, adj=10, set_k_adj=1, set_k_bound=5):
#     obs_list = obs.split("\n")

#     results = query_html(obs_list, query, indexer, k=max(set_k_adj, set_k_bound))
#     results.sort(key=lambda x: obs_list.index(x))

#     output_adj = OrderedSet()
#     for res in results[:set_k_adj]:
#         top_element_index = obs_list.index(res)
#         start = max(top_element_index-adj, 0)
#         end = min(top_element_index+adj, len(obs_list))
#         windowed_obs_adj = obs_list[start:end]
#         for item in windowed_obs_adj:
#             output_adj.add(item)

#     top_element_index_bound = obs_list.index(results[0])
#     bottom_element_index_bound = obs_list.index(results[-1]) + 1
#     windowed_obs_bound = obs_list[top_element_index_bound:bottom_element_index_bound]

#     return results[:set_k_adj], list(output_adj), windowed_obs_bound