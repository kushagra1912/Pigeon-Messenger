# test_client.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from commands import add_contact, send, create_db, view_contacts, recieve, select_contact, invite_contact, accept_request
from models import db
from models.users import Users
from models.keypair import KeyPair
from models.mesages import Message
from models.pending import Pending
import encryption.pigeonhammer as pg
import base64
from networking import server_messages

import uuid

#NOTE: To test, run below in /pigeon-client/client
#poetry run python -m unittest integration-tests

"""
Current test coverage:
- create_db
- select_contact
- add_contact
- view_contacts
- send_request, recieve_requests
- send_message, recieve_message
- encryption & decryption
- invite_contact
- accept_request
"""

def mock_server(msg_json, user_id):
    return msg_json

def mock_send(message, json=""):
    return 0

class TestClientFunctions(unittest.TestCase):
    valid_id = "592b02cf-f520-44d5-9898-2c0dedd32980"
    invalid_id = "Hello" 

    valid_json = {
    "meta": {
        "to": "11111111-1111-1111-1111-111111111111",
        "from": "11111111-1111-1111-1111-111111111112",
        "datetime": "1985-04-12T23:20:50.52Z"
    },
    "message": "i do believe"
    }

    invalid_json = {
        "to": "11111111-1111-1111-1111-111111111111",
        "from": "11111111-1111-1111-1111-111111111112",
        "datetime": "1985-04-12T23:20:50.52Z",
        "message": "i do believe"
    }
    stub_id = "592b02cf-f520-44d5-9898-2c0dedd32888"
    stub_prikey, stub_pubkey = pg.generate_key_pair()
    stub_prikey_str, stub_pubkey_str = pg.serialize_keypair(stub_prikey, stub_pubkey)
    user_id = "592b02cf-f520-44d5-9898-2c0dedd32777"
    # user_pubkey = "user key"

    msg_1 = {
    "meta": {
        "to": user_id,
        "from": stub_id,
        "datetime": "1985-04-12T23:20:50+00:00"
    },
    "message": "hello world"
    }

    def setUp(self):
        self.session = create_db(':memory:')  # Use in-memory database for tests
        self.message = "Pigeons are cool"


    def tearDown(self):
        all = self.session.query(KeyPair).all() + self.session.query(Message).all() + self.session.query(Pending).all() + self.session.query(Users).all()
        for a in all:
            self.session.delete(a)
        self.session.commit()
        self.session.close()


    def create_users(self):
        #Create alice, user
        self.alice = str(uuid.uuid4())
        self.alice_private_key, self.alice_public_key = pg.generate_key_pair()
        self.serial_priv, self.serial_pub = pg.serialize_keypair(self.alice_private_key, self.alice_public_key)
        self.session.add(KeyPair(private_key=self.serial_priv, public_key=self.serial_pub))
        self.session.commit()

        #Create bob, contact
        self.bob = str(uuid.uuid4())
        self.bob_private_key, self.bob_public_key = pg.generate_key_pair()
        _, serial_pub = pg.serialize_keypair(self.bob_private_key, self.bob_public_key)
        # add_contact(self.session, self.bob, serial_pub)


        # test can send & recieve message
    def test_recieve_message(self):
        self.assertEqual(server_messages.send_message(self.msg_1, self.stub_id), 0)
        r = server_messages.recieve_messages(self.user_id)[0]
        self.assertEqual(r.get('from_addr'), self.msg_1.get("meta").get("from"))
        self.assertEqual(r.get('to_addr'), self.msg_1.get("meta").get("to"))
        self.assertEqual(r.get('sent_at'), self.msg_1.get("meta").get("datetime"))
        self.assertEqual(r.get('message'), self.msg_1.get("message"))

    # test can send & recieve invite
    def test_send_invite(self):
        server_messages.send_request(self.stub_id, self.user_id, self.stub_pubkey_str)
        r = server_messages.recieve_requests(self.user_id)[0]
        self.assertEqual(r.get("public_key"), self.stub_pubkey_str)

    def test_invite_sent(self):
        self.create_users()
        
        self.assertTrue(invite_contact(self.session, self.alice, self.bob, self.serial_pub))

        pending = self.session.query(Pending).all()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].uid, self.bob)

    def test_invite_accept(self):
        self.create_users()
        
        self.assertTrue(invite_contact(self.session, self.alice, self.bob, self.serial_pub))

        pending = self.session.query(Pending).all()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].uid, self.bob)
        
        reqs = accept_request(self.session, self.bob)

        users = self.session.query(Users).all()

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].uid, self.alice)
        self.assertEqual(users[0].public_key, self.serial_pub)

        reqs = accept_request(self.session, self.alice)

        pending = self.session.query(Pending).all()
        self.assertEqual(len(pending), 0)
        
        users = self.session.query(Users).all()

        self.assertEqual(len(users), 2)
        self.assertEqual(users[1].uid, self.bob)
        self.assertEqual(users[1].public_key, self.serial_pub)


if __name__ == '__main__':
    unittest.main()

