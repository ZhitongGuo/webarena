import colbert.colbert as colbert
from colbert.infra import Run, RunConfig, ColBERTConfig
from colbert.colbert import Indexer

from colbert.data import Queries
from colbert.colbert import Searcher

import re
import openai
import requests
from colbert.prompt import prompt

API_KEY = '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'
hugging_face_API = "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"
model_id = 'colbert-ir/colbertv2.0'


def query_colbert(payload, model_id, api_token = hugging_face_API):
	headers = {"Authorization": f"Bearer {api_token}"}
	API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

def query_html(html, query, task_id = 1, step = 1, indexer = web_indexer, k = 5):
    # encode each dimension with 2 bits,  truncate passages at 300 tokens, each collection has max 10000 documents
    index_name = f'webarena.{task_id}.step{step}.2bits'
    if isinstance(html, str):
        collection_html = html.split("\n")
    else:
        collection_html = html

    print("#> start indexing")
    with Run().context(RunConfig(nranks=1, experiment='notebook')):
        web_indexer.index(name=index_name, collection=collection_html, overwrite=True)

    print("#> searcher preparing")
    with Run().context(RunConfig(experiment='notebook')):
        web_searcher = Searcher(index=index_name, collection=collection_html)

    print(f"#> {query}")

    results = web_searcher.search(query, k=k)

    for passage_id, passage_rank, passage_score in zip(*results):
        print(f"\t [{passage_rank}] \t\t {passage_score:.1f} \t\t {web_searcher.collection[passage_id]}")

    return [web_searcher.collection[passage_id] for passage_id, passage_rank, passage_score in zip(*results)]


def get_gpt3_5_response(prompt, current, api_key, max_tokens=2048):
    message = [{"role": "system", "content": prompt["intro"]}]
    for (x, y) in prompt["examples"]:
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
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",  # Specify the model here
      messages=message,
      temperature=1.0,
      top_p=0.9,
      # context_length=0,
      max_tokens=384,
      # stop_token=None,
    )

    print(response.choices[0].message.content)
    return response.choices[0].message.content



def get_adj_windowed_obs(obs, query, adj, set_k=1):
    obs_list = obs.split("\n")

    result = query_html(obs_list, query, k=set_k)

    top_element_index = obs_list.index(result[0])

    windowed_obs = obs_list[top_element_index-adj:top_element_index+adj]

    print("\n".join(windowed_obs))
    return windowed_obs


def get_bounded_windowed_obs(obs, query, set_k=5):
    obs_list = obs.split("\n")

    results = query_html(obs_list, query, k= set_k)

    results.sort(key=lambda x: obs_list.index(x))

    numbers = [int(re.search(r"\[(\d+)\]", result).group(1)) for result in results]
    print(numbers)

    top_element_index = obs_list.index(results[0])
    bottom_element_index = obs_list.index(results[-1]) + 1#+ len(results[-1])

    windowed_obs = obs_list[top_element_index:bottom_element_index]

    print("\n".join(windowed_obs))
    return windowed_obs

def start_agent(query, obs, previous_act, prompt = prompt, template = prompt["template"]):
    API_KEY = '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'
    previous_act = None
    obs = input("Enter the current acc tree:")
    windowed_obs = get_adj_windowed_obs(obs, query, 10, set_k=1)
    previous_act = input("Enter previous action:")
    current = template.format(observation = windowed_obs, url = "http://openstreetmap.org", objective = query, previous_action = previous_act)
    response = get_gpt3_5_response(prompt, current, API_KEY)
    return response

if __name__=='__main__':
    nbits = 2   # encode each dimension with 2 bits
    doc_maxlen = 300 # truncate passages at 300 tokens
    max_id = 10000
    checkpoint = 'colbert-ir/colbertv2.0'

    with Run().context(RunConfig(nranks=1, experiment='notebook')):  # nranks specifies the number of GPUs to use
        config = ColBERTConfig(doc_maxlen=doc_maxlen, nbits=nbits, kmeans_niters=4) # kmeans_niters specifies the number of iterations of k-means clustering; 4 is a good and fast default.
                                                                                    # Consider larger numbers for small datasets.
        print("#> initializing Indexer")
        web_indexer = Indexer(checkpoint=checkpoint, config=config)



    query = "Compare the time for walking and driving route from AMC Waterfront to Univ of Pittsburgh"
    obs = open("example_obs.txt", "r").read()
    # windowed_obs = get_adj_windowed_obs(obs, query, 10, set_k=1)
    # previous_act = None
    # current = prompt["template"].format(observation = windowed_obs, url = "http://openstreetmap.org", objective = query, previous_action = previous_act)
    # print(get_gpt3_5_response(prompt, current, API_KEY))
    previous_act = None
    response = start_agent(query, obs, previous_act)
    