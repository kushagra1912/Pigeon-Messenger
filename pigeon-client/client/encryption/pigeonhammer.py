from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64


def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=4096, backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def load_keys(private_key, public_key):
    return load_private_key(private_key), load_public_key(public_key)


def load_public_key(public_key):
    return serialization.load_pem_public_key(public_key.encode(), backend=default_backend())

def load_private_key(private_key):
    return serialization.load_pem_private_key(
        private_key.encode(), password=None, backend=default_backend()
    )


def serialize_keypair(private_key, public_key):
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_key_bytes.decode(), public_key_bytes.decode()


def encrypt_message(message, public_key):
    enc_msg = message.encode()
    padd = padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )
    encrypted_message = public_key.encrypt(
        enc_msg,
        padd,
    )
    return encrypted_message


def crypt_to_str(encoded):
    return base64.b64encode(encoded).decode("utf-8")

def str_to_crypt(str):
    return base64.b64decode(str)


def decrypt_message(encrypted_message, private_key):
    decrypted_message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return decrypted_message.decode()


def sign_message(message, sender_private_key):
    signature = sender_private_key.sign(
        message.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )
    return signature


def atm(message, signature):

    encoded_signature = base64.b64encode(signature).decode("utf-8")
    return f"{message}::{encoded_signature}"


def dfm(signed_message):

    message, encoded_signature = signed_message.rsplit("::", 1)
    signature = base64.b64decode(encoded_signature.encode("utf-8"))
    return message, signature


def verify_signature(message, signature, sender_public_key):
    try:
        sender_public_key.verify(
            signature,
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )
        return True
    except Exception as e:
        return False