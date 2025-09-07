import requests
import uuid
from datetime import datetime, timedelta, timezone

def get_url():
    # for local testing:
    # return 'http://127.0.0.1:8080/api/v1/'

    with open("./api.txt", "r") as f:
        return f.readline()

def validate_id(id):
    try:
        uuid.UUID(str(id))
        return True
    except ValueError:
        return False


def send_message(msg_json, user_id):
    if not validate_id(user_id):
        print("ERROR")
        return 1
    # construct HTTP POST request
    response = requests.post(get_url() + 'messages/' + user_id, json=msg_json)
    return 0

def recieve_messages(user_id):
    # send HTTP GET request
    response = requests.get(get_url() + f'messages/{user_id}')
    if response.status_code == 400:
        print("Error recieving messages")
        return 1
    return response.json()

"""
Send and recieve chat requests
"""
def send_request(from_user_id, to_user_id, public_key):
    
    return requests.post(get_url() + f'messages/{from_user_id}/{to_user_id}/request', json={"public_key": public_key})

def recieve_requests(to_user_id):
    try:
        r = requests.get(get_url() + f'messages/{to_user_id}/request')
    except:
        return None
    if r.status_code != 200:
        return None
    return r.json()