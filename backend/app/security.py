from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from datetime import datetime, timezone
from . import redis_client
import xml.etree.ElementTree as ET
import base64
import json
import os
import re
import hashlib
import struct
import socket
import random
import string
import time


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


class WXBizMsgCryptError(Exception):
    pass


class WXBizMsgCrypt:
    def __init__(self, token: str, encoding_aes_key: str, app_id: str):
        """
        构造函数
        :param token: 公众平台上，开发者设置的Token
        :param encoding_aes_key: 公众平台上，开发者设置的EncodingAESKey
        :param app_id: 企业号的AppId
        """
        try:
            self.key = base64.b64decode(encoding_aes_key + "=")
            assert len(self.key) == 32
        except Exception:
            raise WXBizMsgCryptError("Invalid EncodingAESKey")
        self.token = token
        self.appid = app_id
        self.mode = AES.MODE_CBC

    @staticmethod
    def get_sha1(token, timestamp, nonce, encrypt):
        """
        用SHA1算法生成安全签名
        :param token: 票据
        :param timestamp: 时间戳
        :param nonce: 随机字符串
        :param encrypt: 密文
        :return:
        """
        try:
            sorted_list = sorted([token, timestamp, nonce, encrypt])
            raw = ''.join(sorted_list).encode('utf-8')
            return hashlib.sha1(raw).hexdigest()
        except Exception as e:
            raise WXBizMsgCryptError(f"SHA1 signature error: {e}")

    def encrypt_msg(self, reply_msg: str, nonce: str, timestamp: str = None) -> str:
        """
        将公众号回复用户的消息加密打包
        :param reply_msg: 企业号待回复用户的消息，xml格式的字符串
        :param nonce: 随机串，可以自己生成，也可以用URL参数的nonce
        :param timestamp: 时间戳，可以自己生成，也可以用URL参数的timestamp,如为None则自动用当前时间
        :return: 加密后的xml字符串
        """
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(reply_msg, self.appid)
        if ret != 0:
            raise WXBizMsgCryptError("Encrypt error")

        if not timestamp:
            timestamp = str(int(time.time()))

        signature = self.get_sha1(self.token, timestamp, nonce, encrypt)
        xml = XMLParse.generate(encrypt, signature, timestamp, nonce)
        return xml

    def decrypt_msg(self, post_data: str, msg_signature: str, timestamp: str, nonce: str) -> str:
        """
        检验消息的真实性，并且获取解密后的明文
        :param post_data: 密文，对应POST请求的数据
        :param msg_signature: 签名串，对应URL参数的msg_signature
        :param timestamp: 时间戳，对应URL参数的timestamp
        :param nonce: 随机串，对应URL参数的nonce
        :return: 解密后的明文
        """
        ret, encrypt, _ = XMLParse.extract(post_data)
        if ret != 0:
            raise WXBizMsgCryptError("Extract XML error")

        signature = self.get_sha1(self.token, timestamp, nonce, encrypt)
        if signature != msg_signature:
            raise WXBizMsgCryptError("Signature mismatch")

        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.appid)
        if ret != 0:
            raise WXBizMsgCryptError("Decrypt error")
        return xml_content


class Prpcrypt:
    """提供接收和推送给公众平台消息的加解密接口"""

    def __init__(self, key: bytes):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, text: str, appid: str):
        """
        对明文进行加密
        :param text: 需要加密的明文
        :param appid: 企业号的appid
        :return: 加密得到的字符串
        """
        try:
            # 明文：16位随机字符串
            random_str = self._get_random_str().encode('utf-8')
            # 明文长度（4字节，大端序）
            msg_len = struct.pack("!I", len(text.encode('utf-8')))
            # 原始明文 + AppId（全为utf-8编码的bytes）
            full_text = random_str + msg_len + text.encode('utf-8') + appid.encode('utf-8')

            # PKCS7 补位
            full_text = PKCS7Encoder().encode(full_text)

            # AES 加密
            cipher = AES.new(self.key, AES.MODE_CBC, self.key[:16])
            encrypted = cipher.encrypt(full_text)

            # Base64 编码
            return 0, base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            return -1, None

    def decrypt(self, encrypted: str, appid: str):
        """
        对密文进行解密
        :param encrypted: 密文
        :param appid: 企业号的appid
        :return: 解密得到的明文
        """
        cipher = AES.new(self.key, self.mode, self.key[:16])
        try:
            plain_text = cipher.decrypt(base64.b64decode(encrypted))
        except Exception:
            return -1, None
        try:
            pad = plain_text[-1]
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4:4+xml_len]
            from_appid = content[4+xml_len:].decode('utf-8')
            if from_appid != appid:
                return -1, None
            return 0, xml_content.decode('utf-8')
        except Exception:
            return -1, None

    def _get_random_str(self):
        """
        生成随机字符串
        :return: 生成的16位随机字符串
        """
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


class PKCS7Encoder:
    """提供基于PKCS7算法的加解密接口"""
    block_size = 32

    def encode(self, text: bytes) -> bytes:
        """
        对需要加密的明文进行填充补位
        :param text: 需要进行填充补位操作的明文
        :return: 补齐明文字符串
        """
        pad_len = self.block_size - len(text) % self.block_size
        return text + bytes([pad_len] * pad_len)

    @staticmethod
    def decode(text: bytes) -> bytes:
        """
        删除解密后明文的补位字符
        :param text: 解密后的明文
        :return: 删除补位字符后的明文
        """
        pad_len = text[-1]
        return text[:-pad_len]


class XMLParse:
    """提供提取消息格式中的密文及生成回复消息格式的接口"""
    @staticmethod
    def extract(xml_text: str):
        """
        提取出xml数据包中的加密消息
        :param xml_text: 待提取的xml字符串
        :return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xml_text)
            encrypt = xml_tree.findtext("Encrypt")
            to_user_name = xml_tree.findtext("ToUserName")
            return 0, encrypt, to_user_name
        except Exception:
            return -1, None, None

    @staticmethod
    def generate(encrypt: str, signature: str, timestamp: str, nonce: str) -> str:
        """
        生成xml消息
        :param encrypt: 加密后的消息密文
        :param signature: 安全签名
        :param timestamp: 时间戳
        :param nonce: 随机字符串
        :return: 生成的xml字符串
        """
        return f"""<xml>
<Encrypt><![CDATA[{encrypt}]]></Encrypt>
<MsgSignature><![CDATA[{signature}]]></MsgSignature>
<TimeStamp>{timestamp}</TimeStamp>
<Nonce><![CDATA[{nonce}]]></Nonce>
</xml>"""
