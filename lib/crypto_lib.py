from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import json

def pad(data):
    return data + b' ' * (16 - len(data) % 16)

def encrypt_data(key, plaintext):
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plaintext.encode()))
    iv = base64.b64encode(cipher.iv).decode()
    ct = base64.b64encode(ct_bytes).decode()
    return json.dumps({'iv': iv, 'ciphertext': ct})

def decrypt_data(key, json_input):
    try:
        b64 = json.loads(json_input)
        iv = base64.b64decode(b64['iv'])
        ct = base64.b64decode(b64['ciphertext'])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        pt = cipher.decrypt(ct).rstrip(b' ')
        return pt.decode()
    except:
        return None