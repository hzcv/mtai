import time
import requests
from getpass import getpass
import json

# ---------------- CONFIG ----------------

OWNER_USERNAMES = ["owner_username1", "owner_username2"]  # Replace with real usernames
REPLY_DELAY = 2  # seconds
REPLY_TEXT = "OYY MSG MAT KAR"

# Instagram API settings
INSTAGRAM_API_URL = "https://i.instagram.com/api/v1/"
USER_AGENT = "Instagram 123.0.0.1.100 Android (23/6.0.1; 320dpi; 720x1280; samsung; SM-G930F; herolte; samsungexynos9810; en_US)"

# ---------------- MAIN BOT ----------------

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
owner_ids = []

def ask_credentials():
    username = input("Enter your Instagram username: ")
    password = getpass("Enter your Instagram password: ")
    return username, password

def login_flow():
    username, password = ask_credentials()
    try:
        login_data = {
            "username": username,
            "password": password,
            "device_id": "android-1234567890",
            "from_reg": "false",
            "_csrftoken": "missing",
            "login_attempt_count": "0"
        }
        response = session.post(f"{INSTAGRAM_API_URL}accounts/login/", data=login_data)
        response.raise_for_status()
        session.headers.update({"X-CSRFToken": response.cookies["csrftoken"]})
        user_id = json.loads(response.text)["logged_in_user"]["pk"]
        print(f"[+] Logged in as {username}")
        return user_id
    except requests.exceptions.RequestException as e:
        print("[-] Login failed:", e)
        exit()

def resolve_owner_ids():
    for uname in OWNER_USERNAMES:
        try:
            response = session.get(f"{INSTAGRAM_API_URL}users/{uname}/usernameinfo/")
            response.raise_for_status()
            user_id = json.loads(response.text)["user"]["pk"]
            owner_ids.append(user_id)
        except requests.exceptions.RequestException:
            print(f"[-] Failed to get user ID for owner '{uname}'")

def monitor_groups(self_id):
    print("[✓] Monitoring group chats...")
    replied_message_ids = {}

    while True:
        try:
            response = session.get(f"{INSTAGRAM_API_URL}direct_v2/inbox/")
            response.raise_for_status()
            threads = json.loads(response.text)["inbox"]["threads"]
            for thread in threads:
                thread_id = thread["thread_id"]
                messages = thread["items"]
                messages.reverse()

                for msg in messages:
                    sender_id = msg["user_id"]
                    msg_id = msg["item_id"]

                    if sender_id in owner_ids or sender_id == self_id:
                        continue

                    if msg_id in replied_message_ids.get(thread_id, []):
                        continue

                    # Track that we replied to this message
                    replied_message_ids.setdefault(thread_id, []).append(msg_id)

                    sender_username = msg["user"]["username"]
                    reply = f"@{sender_username} {REPLY_TEXT}"

                    reply_data = {
                        "recipient_users": '["' + thread_id + '"]',
                        "text": reply,
                        "client_context": "1234567890"
                    }
                    response = session.post(f"{INSTAGRAM_API_URL}direct_v2/threads/broadcast/text/", data=reply_data)
                    response.raise_for_status()
                    print(f"[✓] Replied to @{sender_username} in thread {thread_id}")
                    time.sleep(REPLY_DELAY)
        except requests.exceptions.RequestException as e:
            print("[-] Error monitoring groups:", e)
        time.sleep(5)

# ---------------- START ----------------

if __name__ == "__main__":
    self_user_id = login_flow()
    resolve_owner_ids()
    monitor_groups(self_user_id)
