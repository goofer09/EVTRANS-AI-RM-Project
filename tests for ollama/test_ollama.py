import requests, json

response = requests.post('http://localhost:11434/api/generate', json={
    'model': 'mistral:7b',
    'prompt': 'Name 3 car brake components, one per line only.',
    'stream': False, 'temperature': 0.3
})
print(json.dumps(response.json(), indent=2))