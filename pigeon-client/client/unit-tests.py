# unit-tests.py
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from commands import add_contact, send, create_db, view_contacts, recieve, select_contact, invite_contact
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
#poetry run python -m unittest unit-tests

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
        serial_priv, serial_pub = pg.serialize_keypair(self.alice_private_key, self.alice_public_key)
        self.session.add(KeyPair(private_key=serial_priv, public_key=serial_pub))
        self.session.commit()

        #Create bob, contact
        self.bob = str(uuid.uuid4())
        self.bob_private_key, self.bob_public_key = pg.generate_key_pair()
        _, serial_pub = pg.serialize_keypair(self.bob_private_key, self.bob_public_key)
        add_contact(self.session, self.bob, serial_pub)

    def test_rsa_encryption(self):
        private_key, public_key = pg.generate_key_pair()
        enc_message = pg.encrypt_message(self.message, public_key)
        self.assertNotEqual(self.message, enc_message)
        dec_message = pg.decrypt_message(enc_message, private_key)
        self.assertEqual(self.message, dec_message)


    ### network manager tests
    # test message sending
    @patch('requests.post', side_effect=mock_send)
    @patch('networking.server_messages.get_url', return_value="example.com")
    def test_valid_uid(self, mock_send, mock_url):
        self.assertEqual(server_messages.send_message(self.valid_json, self.valid_id), 0)

    @patch('requests.post', side_effect=mock_send)
    def test_invalid_uid(self, mock):
        self.assertEqual(server_messages.send_message(self.valid_json, self.invalid_id), 1)

    @patch('requests.post', side_effect=mock_send)
    @patch('networking.server_messages.get_url', return_value="example.com")
    def test_valid_json(self, mock_send, mock_url):
        self.assertEqual(server_messages.send_message(self.valid_json, self.valid_id), 0)

    @patch('networking.server_messages.send_message', side_effect=mock_server)
    def test_send_encryption(self, mock_server_messages):
        self.create_users()

        #Send from alice to bob
        msg_json = send(self.session, self.alice, self.bob, self.message)

        #Check it is encrypted
        self.assertIsNotNone(msg_json)
        self.assertNotEqual(self.message, msg_json)

        #Decrypt & verify message
        encrypted_data = base64.b64decode(msg_json.get("message").encode("utf-8"))
        dt_msg = pg.decrypt_message(encrypted_data, self.bob_private_key)
        self.assertEqual(self.message, dt_msg)

    def test_view_contacts(self):
        id = str(uuid.uuid4())
        contact = Users(uid=id, public_key=self.stub_pubkey_str)
        self.session.add(contact)
        self.session.commit()
        
        contacts = view_contacts(self.session)
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0].uid, id)
        self.assertEqual(contacts[0].public_key, self.stub_pubkey_str)

    def test_add_contact(self):
        contact_id = str(uuid.uuid4())
        public_key = self.stub_pubkey_str
        add_contact(self.session, contact_id, public_key)
        contact = self.session.query(Users).get(contact_id)
        self.assertIsNotNone(contact)
        self.assertEqual(contact.public_key, public_key)

    def test_select_contact(self):
        user_id = str(uuid.uuid4())
        contact_id = str(uuid.uuid4())

        m1 = 'Hello'
        m2 = 'Hi'
        
        # Add test messages to the database
        message1 = Message(sender=user_id, recipient=contact_id, message=m1)
        message2 = Message(sender=contact_id, recipient=user_id, message=m2)
        self.session.add_all([message1, message2])
        self.session.commit()
        
        messages = select_contact(self.session, user_id, contact_id)
        self.assertEqual(len(messages), 2)

        self.assertEqual(messages[0]['contents']['from'], user_id)
        self.assertEqual(messages[0]['contents']['to'], contact_id)
        self.assertEqual(messages[0]['contents']['message'], m1)

        self.assertEqual(messages[1]['contents']['from'], contact_id)
        self.assertEqual(messages[1]['contents']['to'], user_id)
        self.assertEqual(messages[1]['contents']['message'], m2)

    def test_invite_not_sent(self):
        self.session.add(Pending(uid=self.stub_id))
        
        self.assertFalse(invite_contact(self.session, str(uuid.uuid4()), self.stub_id, self.stub_pubkey_str))

if __name__ == '__main__':
    unittest.main()