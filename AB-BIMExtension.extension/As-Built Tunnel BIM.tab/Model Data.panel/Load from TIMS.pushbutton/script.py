#! python3

import requests
import credentials
from round import Round
from cross_section import CrossSection
from section import Section
from material import Material
import json
import datetime
import os


def authenticate():
    response = requests.post("https://tunnel.big.tuwien.ac.at:8000/api/login/",
                             json={"user": credentials.username, "password": credentials.password})
    access_token = "Bearer " + response.text
    headers = {"Authorization": access_token}
    return headers


def get_sections():
    response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.section/", headers=headers)
    sections = []
    for item in response.json():
        section = Section(item['id'], item['name'])
        sections.append(section)
    return sections


def get_rounds(section_id):
    response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.tunnel.round/?q=[[\"section\", \"=\", {}]]".format(section_id), headers=headers)
    rounds = []
    for item in response.json():
        if item['comment'] is None:
            item['comment'] = ''
        round = Round(item['id'], item['start_chainage'], item['end_chainage'], 'Kalotte', item['comment'])
        rounds.append(round)
    return rounds


def get_material(round_id):
    round_activity_ids = get_round_activity_ids(round_id)
    response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.tunnel.measure/?q=[[\"activity\", \"in\", {}]]".format(round_activity_ids), headers=headers)
    materials = []
    for item in response.json():
        material = Material(item['measure_definition.']['name'], item['uom.']['name'], item['quantity'])
        materials.append(material)
    return materials


def get_round_activity_ids(round_id):
    response = requests.get("https://tunnel.big.tuwien.ac.at:8000/api/construction.activity/?q=[[\"round\",\"=\",{}]]".format(round_id), headers=headers)
    activity_ids = []
    for item in response.json():
        activity_ids.append(item['id'])
    return activity_ids


def get_data():
    sections = get_sections()
    for section in sections:
        rounds = get_rounds(section.id)
        rounds = sorted(rounds, key=lambda x: x.start_meter)
        for round in rounds:
            round_material = get_material(round.id)
            round.material = serialize_data(round_material)
        section.rounds = (serialize_data(rounds))
    return {"sections": serialize_data(sections)}


def serialize_data(data_list):
    result = []
    for item in data_list:
        result.append(vars(item))
    return result


def store_data(data):
    file_path = create_file_path()
    with open(file_path, 'w') as f:
        json.dump(data, f, ensure_ascii=True)
        print("Data was successfully stored!")


def create_file_path():
    absolute_path_of_script = os.path.dirname(__file__)
    absolute_file_path = get_parent_dir(get_parent_dir(get_parent_dir(absolute_path_of_script)))
    return absolute_file_path + '\\data\\tims' + get_current_timestamp() + '.json'


def get_current_timestamp():
    current_datetime = datetime.datetime.now()
    timestamp_string = current_datetime.strftime("%d%m%Y_%H%M%S")
    return timestamp_string


def get_parent_dir(directory):
    return os.path.dirname(directory)


headers = authenticate()
data = get_data()
store_data(data)

