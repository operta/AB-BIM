#! python3

import requests

response = requests.post("https://tunnel.big.tuwien.ac.at:8000/api/login/", json={"user": "admin","password": "admin"})
access_token = "Bearer " + response.text
headers = {"Authorization": access_token}

response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.tunnel.support.definition/", headers=headers)
support_definitions = response.json()

print(support_definitions)