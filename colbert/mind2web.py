from colbert import Indexer, Searcher
from colbert.infra import Run, RunConfig, ColBERTConfig
from colbert.data import Queries, Collection
import pandas as pd
from tqdm import tqdm

from sortedcollections import OrderedSet
import csv
import argparse
import openai
import re

def query_html(html, query, indexer, task_id = 1, k = 5):
    # encode each dimension with 2 bits,  truncate passages at 300 tokens, each collection has max 10000 documents
    # index_name = f'webarena.{task_id}.step{step}.2bits'
    index_name = f'mind2web.{task_id}.2bits'

    if isinstance(html, str):
        collection_html = html.split("\n")
    else:
        collection_html = html

    # print("#> start indexing")
    with Run().context(RunConfig(nranks=1, experiment='notebook')):
        web_indexer.index(name=index_name, collection=collection_html, overwrite=True)

    # print("#> searcher preparing")
    with Run().context(RunConfig(experiment='notebook')):
        web_searcher = Searcher(index=index_name, collection=collection_html)

    # print(f"#> {query}")

    results = web_searcher.search(query, k=k)

    # for passage_id, passage_rank, passage_score in zip(*results):
    #     print(f"\t [{passage_rank}] \t\t {passage_score:.1f} \t\t {web_searcher.collection[passage_id]}")

    return [web_searcher.collection[passage_id] for passage_id, passage_rank, passage_score in zip(*results)]

def get_adj_windowed_obs(obs, query, indexer, adj = 5, set_k=1):
    obs_list = obs.split("\n")

    results = query_html(obs_list, query, indexer, k=set_k)
    results.sort(key=lambda x: obs_list.index(x))

    output = OrderedSet()
    added_indices = set()
    for res in results:
        n = len(res)
        top_element_index = obs_list.index(res)
        start = max(top_element_index-adj, 0)
        end = min(top_element_index+adj, n)
        windowed_obs = obs_list[start:end]
        for item in windowed_obs:
            output.add(item)  

    # print("\n".join(windowed_obs))
    return list(output)


def get_bounded_windowed_obs(obs, query, indexer, set_k=5):
    obs_list = obs.split("\n")

    results = query_html(obs_list, query,indexer, k= set_k)

    results.sort(key=lambda x: obs_list.index(x))

    # numbers = [int(re.search(r"\[(\d+)\]", result).group(1)) for result in results]
    # print(numbers)

    top_element_index = obs_list.index(results[0])
    bottom_element_index = obs_list.index(results[-1]) + 1#+ len(results[-1])

    windowed_obs = obs_list[top_element_index:bottom_element_index]

    # print("\n".join(windowed_obs))
    return windowed_obs

def get_windowed_obs(obs, query, indexer, adj=10, set_k_adj=1, set_k_bound=5):
    obs_list = obs.split("\n")

    results = query_html(obs_list, query, indexer, k=max(set_k_adj, set_k_bound))
    results.sort(key=lambda x: obs_list.index(x))

    output_adj = OrderedSet()
    for res in results[:set_k_adj]:
        top_element_index = obs_list.index(res)
        start = max(top_element_index-adj, 0)
        end = min(top_element_index+adj, len(obs_list))
        windowed_obs_adj = obs_list[start:end]
        for item in windowed_obs_adj:
            output_adj.add(item)

    top_element_index_bound = obs_list.index(results[0])
    bottom_element_index_bound = obs_list.index(results[-1]) + 1
    windowed_obs_bound = obs_list[top_element_index_bound:bottom_element_index_bound]

    return results[:set_k_adj], list(output_adj), windowed_obs_bound


def save_last_processed_index(index):
    with open("last_processed_index.txt", "w") as f:
        f.write(str(index))

def load_last_processed_index():
    try:
        with open("last_processed_index.txt", "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0

def check_action_in_obs(obs, action):
    obs = "\n".join(obs)
    action_number = action.split(' ')[-1]
    return action_number in obs




# updated_df = query_gpt_and_check(df, 'gpt-3.5-turbo')  # Use the appropriate GPT model

if __name__=='__main__':
    nbits = 2   # encode each dimension with 2 bits
    doc_maxlen = 300 # truncate passages at 300 tokens
    max_id = 10000
    checkpoint = 'colbert-ir/colbertv2.0'

    parser = argparse.ArgumentParser(description='Process a specific number of indices.')
    parser.add_argument('--num_indices', type=int, default=100, help='Number of indices to process')
    args = parser.parse_args()

    with Run().context(RunConfig(nranks=1, experiment='notebook')):  # nranks specifies the number of GPUs to use
        config = ColBERTConfig(doc_maxlen=doc_maxlen, nbits=nbits, kmeans_niters=4) # kmeans_niters specifies the number of iterations of k-means clustering; 4 is a good and fast default.
                                                                                    # Consider larger numbers for small datasets.
        print("#> initializing Indexer")
        web_indexer = Indexer(checkpoint=checkpoint, config=config)

    #OBSERVATION,OBJECTIVE,PREVIOUS ACTIONS,ACTION
    mind2web_data = pd.read_csv("mind2web_all_1031.csv")
    adj_size = 10
    set_k = 5

    last_processed_index = load_last_processed_index()
    mode = 'a' if last_processed_index > 0 else 'w'


    with open(f"sub_mind2web.csv", mode=mode, newline='') as file:
        writer = csv.writer(file)
        
        if last_processed_index == 0:
            writer.writerow(['query', 'obs', 'action', 'results', 'windowed_obs', 'bounded_obs', 'compression_rate_adj', 'compression_rate_bound', 'correct_count_adj', 'correct_count_bound'])
    
        for i, row in tqdm(enumerate(mind2web_data.iterrows()), total=mind2web_data.shape[0]):
            if i >= args.num_indices:  # Process only the specified number of rows
                break

            index, data = row
            if index < last_processed_index:
                continue

            query = data["OBJECTIVE"]
            obs = data["OBSERVATION"]
            action = data["ACTION"]
            
            results, windowed_obs, bounded_obs = get_windowed_obs(obs, query, web_indexer, adj=10, set_k_adj=1, set_k_bound=5)
            results = '\n'.join(results)

            compression_rate_adj = len(windowed_obs) / len(obs.split("\n"))
            compression_rate_bound = len(bounded_obs) / len(obs.split("\n"))
            
            correct_count_adj = 1 if check_action_in_obs(windowed_obs, action) else 0
            correct_count_bound = 1 if check_action_in_obs(bounded_obs, action) else 0
            
            writer.writerow([query, obs, action, results, windowed_obs, bounded_obs, compression_rate_adj, compression_rate_bound, correct_count_adj, correct_count_bound])
            file.flush()

            save_last_processed_index(index)


    # see if ACTION is in the windowed_obs, and get the final accuracy

    # previous_act = None
    # current = prompt["template"].format(observation = windowed_obs, url = "http://openstreetmap.org", objective = query, previous_action = previous_act)
    # print(get_gpt3_5_response(prompt, current, API_KEY))
    
    
   