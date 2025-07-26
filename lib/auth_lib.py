import os
import json
import hashlib
import base64

def create_user(username, password):
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    key_hash = hashlib.sha256(key).hexdigest()
    data = {
        "salt": base64.b64encode(salt).decode(),
        "key_hash": key_hash
    }
    os.makedirs("users", exist_ok=True)
    with open(f"users/{username}.json", "w") as f:
        json.dump(data, f)
    return key

def verify_user(username, password):
    try:
        with open(f"users/{username}.json") as f:
            data = json.load(f)
        salt = base64.b64decode(data["salt"])
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        key_hash = hashlib.sha256(key).hexdigest()
        if key_hash == data.get("key_hash"):
            return key
        else:
            return None
    except FileNotFoundError:
        return None