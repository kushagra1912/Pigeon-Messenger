from encryption import pigeonhammer as pg
from networking import server_messages
import threading
import uuid
import os
import random
import time
from datetime import datetime, timedelta, timezone
from commands import *

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker

from models import db
from models.mesages import Message
from models.users import Users
from models.pending import Pending
from models.keypair import KeyPair

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

selected_friend = None

OPTIONS = """Options:
\\list           list pigeon contacts
\\select <id>    select contact with <id> to message
\\add <id>      invite a pigeon user with <id> to be a contact
\\options        print these options
Anything entered besides the above will be considered a message and will be sent."""
BAD_CMD = "Invalid command."
NO_SELECT = "No contact selected."

def input_thread(session, pigeon_id, public_key_str):
    """
    The input thread for the client, constantly takes in user input from stdin.
    """
    while True:
        args = input()
        global selected_friend
        if args.startswith("\\list"):
            contacts = view_contacts(session)
            if not contacts:
                print("You have no contacts")
                print()
                continue
            print("These are your contacts:")
            for c in contacts:
                print(c.to_dict()["id"])
            print()
            continue
        elif args.startswith("\\select"):
            parts = args.split()
            if len(parts) != 2:
                print(BAD_CMD)
                continue
            #Check they are a contact
            contacts = view_contacts(session)
            if not contacts:
                print("You have no contacts")
                print()
                continue
            for c in contacts:
                if c.to_dict()["id"] == parts[1]:
                    friend_id = parts[1]
                    selected_friend = friend_id
                    continue
            if not selected_friend:
                print(parts[1] + "is not a contact")
                print()
                continue
            history = select_contact(session, pigeon_id, selected_friend)
            for m in history:
                sender = m["contents"]["from"]
                at = m["created_at"]
                body = m["contents"]["message"]
                print(f"{sender} [{at}] $ {body}")
            continue
        elif args.startswith("\\add"):
            parts = args.split()
            if len(parts) != 2:
                print(BAD_CMD)
                continue
            invite_contact(session, pigeon_id, parts[1], public_key_str)
            print()
            continue
        elif args == "\\options":
            print()
            print(OPTIONS)
            print()
            continue
        elif selected_friend:
            send(session, pigeon_id, friend_id, args)
        else:
            print("You have not selected a contact to message")
            print()

def receive_thread(session, pigeon_id):
    """
    The output thread for the client, constantly receiving requests
    """
    while True:   
        accept_request(session, pigeon_id)
        global selected_friend
        if selected_friend:
            recieved = recieve(session, pigeon_id, selected_friend)
            if recieved:
                for msg in recieved:
                    print(f"{selected_friend} ({msg.get('sent_at')}): " + msg.get("message"))
        time.sleep(5)


def run():
    session = create_db()

    # get user id or generate one
    pigeon_id = ""
    try:
        with open("pigeon_id.txt", "r") as id:
            pigeon_id = id.readline()
    except:
        with open("pigeon_id.txt", "w") as id:
            pigeon_id = str(uuid.uuid4())
            id.write(pigeon_id)

    # get keypair or generate keypair if it does not exist
    private_key = None
    public_key = None
    private_key_str = None
    public_key_str = None
    keys = session.query(KeyPair).all()
    if not keys:
        private_key, public_key = pg.generate_key_pair()
        private_key_str, public_key_str = pg.serialize_keypair(private_key, public_key)
        session.add(KeyPair(private_key=private_key_str, public_key=public_key_str))
        session.commit()
    else:
        key = keys[0]
        private_key_str = key.private_key
        public_key_str = key.public_key
        private_key, public_key = pg.load_keys(private_key_str, public_key_str)

    print(f"Welcome user {pigeon_id} to Pigeon, the super secret instant messanger!")
    print(OPTIONS)
    print()
    print(NO_SELECT)

    inputThread = threading.Thread(target=input_thread, args=(session, pigeon_id, public_key_str))
    inputThread.daemon = True
    inputThread.start()
    receiveThread = threading.Thread(target=receive_thread, args=(session, pigeon_id))
    receiveThread.daemon = True
    receiveThread.start()
    while True:
        continue

if __name__ == "__main__":
    run()
