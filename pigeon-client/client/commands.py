from encryption import pigeonhammer as pg
from networking import server_messages
import threading
import uuid
import os
import random
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker

from models import db
from models.mesages import Message
from models.users import Users
from models.pending import Pending
from models.keypair import KeyPair


def create_db(config_overrides=None):
    engine = create_engine("sqlite:///pigeondb.db")

    db.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def select_contact(session, user_id, selected_friend):
    """
    Return the chat history of the selected contact in order of sent and recieved datetimes
    """
    sent_list = (
        session.query(Message)
        .filter(Message.sender == user_id, Message.recipient == selected_friend)
        .all()
    )
    recieved_list = (
        session.query(Message)
        .filter(Message.sender == selected_friend, Message.recipient == user_id)
        .all()
    )
    
    all_sorted = [d.to_dict() for d in sent_list + recieved_list]
    all_sorted = sorted(all_sorted, key=lambda x: x["mid"])
    print("Now messaging " + selected_friend)
    return all_sorted

def add_contact(session, contact_id, public_key):
    """
    Add the contacts id and public key to the session database.
    """
    new_contact = Users(uid=contact_id, public_key=public_key)
    session.add(new_contact)
    session.commit()
    print(contact_id + " has been added as a contact")
    print()

def invite_contact(session, my_id, their_id, my_public_key):
    """
    Invite the user id as a contact
    """
    p = session.query(Pending).get(their_id)
    if not p:
        server_messages.send_request(my_id, their_id, my_public_key)
        session.add(Pending(uid=their_id))
        session.commit()
        print(f"Contact {their_id} has been invited to be a friend")
        return True
    else:
        print(f"Invite has already been sent to contact {their_id}")
        return False

def view_contacts(session):
    """
    Return a list of all contacts
    """
    contacts = session.query(Users).all()
    return contacts

def send(session, user_id, reciever_id, message):
    """
    encrypt the selected message
    store message in the database
    send message to server
    """
    # Get Keys
    receiver_key_pair = session.query(Users).get(reciever_id)
    sender_key_pair = session.query(KeyPair).first()

    if not receiver_key_pair:
        print(f"Do not have {reciever_id} public key yet")
        return

    receiver_public_key = pg.load_public_key(receiver_key_pair.public_key)
    sender_private_key = pg.load_private_key(sender_key_pair.private_key)

    e_message = pg.crypt_to_str(pg.encrypt_message(message, receiver_public_key))

    time = datetime.now()
    str_time = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # construct json body
    msg_json = {
        "meta": {
            "to": reciever_id,
            "from": user_id,
            "datetime": str_time,
        },
        "message": e_message,
    }

    # add message to db
    new_message = Message(
        created_at=time, sender=user_id, recipient=reciever_id, message=message
    )
    session.add(new_message)
    session.commit()
    return server_messages.send_message(msg_json, user_id)

def recieve(session, user_id, sender_id):
    """
    poll server for new messages
    store new messages in the database
    decrypt the new messages for the selected contact
    return the list of decrypted new messages
    """
    new_msgs = server_messages.recieve_messages(user_id)
    sender_msgs = []

    my_private_key = pg.load_private_key(session.query(KeyPair).first().private_key)

    for msg in new_msgs:
        # get sender public key
        sender = msg.get("from_addr")
        sender_key_pair = session.query(Users).get(sender)

        if not sender_key_pair:
            print(f"Do not have {sender} public key yet")
            return None

        sender_public_key = pg.load_public_key(sender_key_pair.public_key)

        # decrypt & verify message
        msg_text = msg.get("message")
        dt_msg = pg.decrypt_message(pg.str_to_crypt(msg_text), my_private_key)

        dec_msg = {
            "to_addr": msg.get('to_addr'),
            "from_addr": sender,
            "sent_at": datetime.fromisoformat(msg.get('sent_at')),
            "message": dt_msg,
        }
        # if message is from contact, collect them all
        if sender == sender_id:
            sender_msgs.append(dec_msg)

        # add message to db
        new_message = Message(
            created_at=datetime.fromisoformat(msg.get("sent_at")),
            sender=msg.get("from_addr"),
            recipient=msg.get("to_addr"),
            message=dec_msg.get("message"),
        )
        session.add(new_message)
        session.commit()
    return sender_msgs

def accept_request(session, user_id):

    reqs = server_messages.recieve_requests(user_id)
    if reqs:
        for r in reqs:
            sender = r.get("from_pigeon_id")
            key = r.get("public_key")
            pend = session.query(Pending).get(sender)
            # if sender is in pending, we remove them from pending and add them to contacts (User db)
            if pend:
                session.delete(pend)
                session.commit()
                add_contact(session, sender, key)

            # if sender is not in pending, it means we add them to Users and send invite
            else:
                add_contact(session, sender, key)
                # invite_contact(session, user_id, sender, session.query(KeyPair).first().public_key)
                server_messages.send_request(user_id, sender, session.query(KeyPair).first().public_key)

