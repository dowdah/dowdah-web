from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from datetime import datetime, timezone
from . import redis_client
import base64
import json
import os
import re


AES_GCM_SECRET = os.environ.get('SECRET_KEY')
TURNSTILE_EXPIRATION = 300  # Turnstile 参数有效期(秒)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def decrypt_str(encrypted_str: str):
    encrypted_str = base64.b64decode(encrypted_str)
    iv = encrypted_str[:12]
    ciphertext = encrypted_str[12:-16]
    tag = encrypted_str[-16:]
    cipher = AES.new(AES_GCM_SECRET.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    decrypted_str = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_str.decode('utf-8')


def decrypt_json(encrypted_data: str):
    encrypted_bytes = base64.b64decode(encrypted_data)
    iv = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:-16]
    tag = encrypted_bytes[-16:]
    cipher = AES.new(AES_GCM_SECRET.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    return json.loads(decrypted_data.decode('utf-8'))


def encrypt_str(encrypted_str: str):
    iv = get_random_bytes(12)
    cipher = AES.new(AES_GCM_SECRET.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(encrypted_str.encode('utf-8'))
    encrypted_str = iv + ciphertext + tag
    return base64.b64encode(encrypted_str).decode('utf-8')


def encrypt_json(encrypted_data: dict):
    iv = get_random_bytes(12)
    cipher = AES.new(AES_GCM_SECRET.encode('utf-8'), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(encrypted_data).encode('utf-8'))
    encrypted_data = iv + ciphertext + tag
    return base64.b64encode(encrypted_data).decode('utf-8')


def verify_turnstile(encrypted_turnstile_response, fingerprint, action=None):
    if redis_client.get(encrypted_turnstile_response):
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Turnstile response has been used'
        }
    else:
        try:
            turnstile_response = decrypt_json(encrypted_turnstile_response)
        except:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Invalid turnstile response'
            }
        else:
            if action is not None and action not in turnstile_response['action']:
                response_json = {
                    'success': False,
                    'code': 400,
                    'msg': 'Action mismatch'
                }
            else:
                if turnstile_response['cdata'] != fingerprint:
                    response_json = {
                        'success': False,
                        'code': 400,
                        'msg': 'Fingerprint mismatch'
                    }
                else:
                    challenge_time = datetime.strptime(turnstile_response['challenge_ts'],
                                                       "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                    time_diff = (datetime.now(timezone.utc) - challenge_time).total_seconds()
                    if time_diff > TURNSTILE_EXPIRATION:
                        response_json = {
                            'success': False,
                            'code': 400,
                            'msg': 'Turnstile response has expired'
                        }
                    else:
                        redis_client.set(encrypted_turnstile_response, 'used', ex=TURNSTILE_EXPIRATION)
                        response_json = {
                            'success': True,
                            'code': 200,
                            'msg': 'Turnstile response verified'
                        }
    return response_json


def verify_email_code(email, code):
    if EMAIL_REGEX.match(email):
        if redis_client.get(f"email_verification_{email}") == code:
            response_json = {
                'success': True,
                'code': 200,
                'msg': 'Email verification code verified'
            }
            redis_client.delete(f"email_verification_{email}")
        else:
            response_json = {
                'success': False,
                'code': 400,
                'msg': 'Incorrect email verification code'
            }
    else:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Invalid email address'
        }
    return response_json
