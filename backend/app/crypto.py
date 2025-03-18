from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json


def decrypt_str(secret_key: str, encrypted_str: str):
    encrypted_str = base64.b64decode(encrypted_str)
    iv = encrypted_str[:12]
    ciphertext = encrypted_str[12:-16]
    tag = encrypted_str[-16:]
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    decrypted_str = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_str.decode('utf-8')


def decrypt_json(secret_key: str, encrypted_data: str):
    encrypted_bytes = base64.b64decode(encrypted_data)
    iv = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:-16]
    tag = encrypted_bytes[-16:]
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(decrypted_data.decode('utf-8'))


def encrypt_str(secret_key: str, encrypted_str: str):
    iv = get_random_bytes(12)
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(encrypted_str.encode('utf-8'))
    encrypted_str = iv + ciphertext + tag
    return base64.b64encode(encrypted_str).decode('utf-8')


def encrypt_json(secret_key: str, encrypted_data: dict):
    iv = get_random_bytes(12)
    cipher = AES.new(secret_key.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(encrypted_data).encode('utf-8'))
    encrypted_data = iv + ciphertext + tag
    return base64.b64encode(encrypted_data).decode('utf-8')
