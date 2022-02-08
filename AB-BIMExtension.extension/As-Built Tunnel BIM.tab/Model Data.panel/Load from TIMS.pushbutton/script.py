#! python3

import requests
import credentials
from round import Round
from cross_section import CrossSection


def authenticate():
    response = requests.post("https://tunnel.big.tuwien.ac.at:8000/api/login/",
                             json={"user": credentials.username, "password": credentials.password})
    access_token = "Bearer " + response.text
    headers = {"Authorization": access_token}
    return headers


def get_rounds(headers):
    response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.tunnel.round/", headers=headers)
    rounds = []
    for item in response.json():
        round = Round(item['start_chainage'], item['end_chainage'], CrossSection.KALLOTE)
        rounds.append(round)
    return rounds


def get_data():
    headers = authenticate()
    rounds = get_rounds(headers)
    rounds = sorted(rounds, key=lambda x: x.start_meter)
    return rounds


print(get_data())