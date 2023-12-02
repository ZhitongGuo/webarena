import requests
import pandas as pd

df = pd.read_csv("preprocessed_mind2web.csv")
obs = df.iloc[1,1].split('\n')
query = df.iloc[1,0]

# Define the endpoint
url = "http://localhost:5001/search"

# Define your search request data
data = {
    "obs": obs, 
    "query": query,
    "task_id": 1,
    "k": 5
}

# Make the POST request
response = requests.post(url, json=data)

# Check if the request was successful
if response.status_code == 200:
    print("Search Results:", response.json())
else:
    print("Error:", response.text)
