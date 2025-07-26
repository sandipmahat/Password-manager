# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pycryptodome",
# ]
# ///
import json
import os
import getpass
import time
import msvcrt

from lib.auth_lib import create_user, verify_user
from lib.crypto_lib import encrypt_data, decrypt_data

DB_FILE = "db.json"
LOCK_FILE = "locked_users.json"
SESSION_FILE = "session.json"
SESSION_TIMEOUT = 300

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE) as f:
        content = f.read().strip()
        if not content:
            return {}
        return json.loads(content)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_locked_users():
    if not os.path.exists(LOCK_FILE):
        return {}
    with open(LOCK_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_locked_users(data):
    with open(LOCK_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_session(username):
    session_data = {
        "username": username,
        "login_time": int(time.time())
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    with open(SESSION_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def print_help(context="main"):
    clear_screen()
    if context == "main":
        print("""
==========================
         HELP
==========================
- 1: Register new account
- 2: Login to your account
- 3: Exit application
- h: Show this help menu
""")
    elif context == "dashboard":
        print("""
===================================
            HELP
===================================
- 1: Save new password
- 2: View saved passwords
- 3: Logout (ends session)
- q: Quit application
- h: Show this help menu
""")
    elif context == "submenu":
        print("""
===================================
            HELP
===================================
- ESC: Go back to dashboard
- h: Show this help menu
""")
    input("\nPress Enter to continue...")
    clear_screen()

def wait_for_key(valid_keys=None, esc_back=False):
    """
    Wait for a key press and return it.
    If esc_back is True, ESC key returns 'esc'.
    """
    while True:
        key = msvcrt.getch()
        if key in [b'\x1b'] and esc_back:
            return 'esc'
        if key in [b'h', b'H']:
            return 'h'
        if valid_keys and key.decode() in valid_keys:
            return key.decode()
        if not valid_keys:
            return key.decode()

def register():
    clear_screen()
    print("=== Register New Account ===")
    username = input("New Username: ")
    password = getpass.getpass("New Password: ")
    key = create_user(username, password)
    print(f"\nUser '{username}' created successfully!")
    input("\nPress Enter to continue...")
    clear_screen()

def login():
    clear_screen()
    print("=== Login ===")
    attempts = 0
    max_attempts = 3
    lockout_time = 30

    locked_users = load_locked_users()

    username = input("Username: ")

    user_file = f"users/{username}.json"
    if not os.path.exists(user_file):
        print("\nUser does not exist.")
        input("\nPress Enter to continue...")
        clear_screen()
        return
    try:
        with open(user_file) as f:
            data = f.read().strip()
            if not data:
                print("\nUser data is corrupted or empty.")
                input("\nPress Enter to continue...")
                clear_screen()
                return
    except Exception:
        print("\nUser data is corrupted.")
        input("\nPress Enter to continue...")
        clear_screen()
        return

    if username in locked_users:
        unlock_time = locked_users[username]
        now = int(time.time())
        if now < unlock_time:
            remaining = unlock_time - now
            print(f"\nUser '{username}' is locked. Try again in {remaining} seconds.")
            input("\nPress Enter to continue...")
            clear_screen()
            return
        else:
            del locked_users[username]
            save_locked_users(locked_users)

    while attempts < max_attempts:
        password = getpass.getpass("Password: ")
        key = verify_user(username, password)
        if key:
            save_session(username)
            clear_screen()
            dashboard(username, key)
            return
        else:
            attempts += 1
            print(f"\nInvalid credentials. Attempt {attempts}/{max_attempts}.")
            if attempts < max_attempts:
                input("\nPress Enter to try again...")
                clear_screen()

    locked_users[username] = int(time.time()) + lockout_time
    save_locked_users(locked_users)
    print(f"\nToo many failed attempts. User '{username}' locked for {lockout_time} seconds.")
    input("\nPress Enter to continue...")
    clear_screen()

def dashboard(username, key):
    session = load_session()
    if session and session.get("username") == username:
        session_start = session.get("login_time", int(time.time()))
    else:
        session_start = int(time.time())

    while True:
        clear_screen()
        print(f"Welcome, {username}!\n")
        print("="*35)
        print("      PASSWORD MANAGER DASHBOARD")
        print("="*35)
        print("1. Save New Password")
        print("2. View Saved Passwords")
        print("3. Logout")
        print("="*35)
        print("Press 'q' to quit, 'h' for help.")
        print("="*35)
        print("Choose an option: ", end="", flush=True)

        choice = wait_for_key(valid_keys=['1', '2', '3', 'q', 'Q', 'h', 'H'])
        if choice in ['h', 'H']:
            print_help("dashboard")
            continue
        if choice in ['q', 'Q']:
            clear_screen()
            print("Quitting application. Goodbye!")
            exit(0)
        if choice == '3':
            clear_session()
            clear_screen()
            print("Logged out successfully.")
            time.sleep(1)
            clear_screen()
            break
        if time.time() - session_start > SESSION_TIMEOUT:
            clear_session()
            print("\nSession expired. Please login again.")
            time.sleep(2)
            clear_screen()
            break
        if choice == '1':
            save_password(username, key, session_start)
        elif choice == '2':
            view_passwords(username, key, session_start)

def get_input_with_esc(prompt):
    """Get input from user, allow ESC to cancel and return None."""
    print(prompt, end="", flush=True)
    chars = []
    while True:
        ch = msvcrt.getch()
        if ch == b'\x1b':
            print()
            return None
        elif ch in [b'\r', b'\n']:
            print()
            return ''.join(chars)
        elif ch == b'\x08':
            if chars:
                chars.pop()
                print('\b \b', end='', flush=True)
        else:
            try:
                c = ch.decode()
                chars.append(c)
                print(c, end='', flush=True)
            except:
                pass

def get_password_with_esc(prompt):
    """Get password input from user, allow ESC to cancel and return None."""
    print(prompt, end="", flush=True)
    chars = []
    while True:
        ch = msvcrt.getch()
        if ch == b'\x1b':
            print()
            return None
        elif ch in [b'\r', b'\n']:
            print()
            return ''.join(chars)
        elif ch == b'\x08':
            if chars:
                chars.pop()
                print('\b \b', end='', flush=True)
        else:
            try:
                c = ch.decode()
                chars.append(c)
                print('*', end='', flush=True)
            except:
                pass

def save_password(username, key, session_start):
    while True:
        clear_screen()
        print("=== Save New Password ===")
        print("Press ESC at any prompt to go back.\n")
        site = get_input_with_esc("Website: ")
        if site is None:
            break
        site_user = get_input_with_esc("Site Username: ")
        if site_user is None:
            break
        site_pass = get_password_with_esc("Site Password: ")
        if site_pass is None:
            break
        db = load_db()
        if username not in db:
            db[username] = []
        enc_user = encrypt_data(key, site_user)
        enc_pass = encrypt_data(key, site_pass)
        db[username].append({"site": site, "username": enc_user, "password": enc_pass})
        save_db(db)
        print("\nPassword saved successfully!")
        print("Press ESC to go back, 'h' for help, or any key to save another.")
        k = wait_for_key(esc_back=True)
        if k == 'esc':
            break
        if k == 'h':
            print_help("submenu")
        if time.time() - session_start > SESSION_TIMEOUT:
            clear_session()
            print("\nSession expired. Please login again.")
            time.sleep(2)
            clear_screen()
            break

def view_passwords(username, key, session_start):
    while True:
        clear_screen()
        print("=== Saved Passwords ===")
        print("Press ESC to go back, 'h' for help.")
        entries = load_db().get(username, [])
        if not entries:
            print("No passwords saved yet.")
        else:
            for idx, entry in enumerate(entries, 1):
                print(f"\n[{idx}] Site: {entry['site']}")
                dec_user = decrypt_data(key, entry['username'])
                dec_pass = decrypt_data(key, entry['password'])
                print(f"    Username: {dec_user}")
                print(f"    Password: {dec_pass}")
        print("\nPress ESC to go back, 'h' for help, or any key to refresh.")
        k = wait_for_key(esc_back=True)
        if k == 'esc':
            break
        if k == 'h':
            print_help("submenu")
        if time.time() - session_start > SESSION_TIMEOUT:
            clear_session()
            print("\nSession expired. Please login again.")
            time.sleep(2)
            clear_screen()
            break

def main():
    session = load_session()
    if session:
        username = session.get("username")
        login_time = session.get("login_time")
        if username and login_time and (time.time() - login_time) < SESSION_TIMEOUT:
            user_file = f"users/{username}.json"
            if os.path.exists(user_file):
                print(f"Resuming session for '{username}'.")
                password = getpass.getpass("Enter your password to unlock session: ")
                key = verify_user(username, password)
                if key:
                    dashboard(username, key)
                else:
                    clear_session()
                    print("Invalid password. Session cleared.")
                    time.sleep(2)
                    clear_screen()
    while True:
        clear_screen()
        print("""
==========================
   CLI Password Manager
==========================
1. Register
2. Login
3. Exit
Press 'h' for help.
""")
        print("Select: ", end="", flush=True)
        choice = wait_for_key(valid_keys=['1', '2', '3', 'h', 'H'])
        if choice in ['h', 'H']:
            print_help("main")
            continue
        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            clear_screen()
            print("Goodbye!")
            break

if __name__ == "__main__":
    main()