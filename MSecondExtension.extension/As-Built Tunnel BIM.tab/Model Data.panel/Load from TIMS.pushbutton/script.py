#! python3

import requests
import credentials


def authenticate():
    response = requests.post("https://tunnel.big.tuwien.ac.at:8000/api/login/",json={"user": credentials.username, "password": credentials.password})
    access_token = "Bearer " + response.text
    headers = {"Authorization": access_token}
    return headers

