from kiteconnect import KiteConnect
from dotenv import load_dotenv
import os


# Load from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TOKEN_FILE = "access_token.txt"

# Initialize Kite

kite = KiteConnect(api_key=API_KEY)

# Step 1: Generate login URL
print("Login here to get your request_token:")
print(kite.login_url())

# Step 2: Paste request_token manually after login
request_token = input("Paste the request_token here: ").strip()

# Step 3: Generate access_token and save it
try:
    session_data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = session_data["access_token"]

    # Save token to a file
    with open(TOKEN_FILE, "w") as f:
        f.write(access_token)

    print("Access token saved successfully.")
except Exception as e:
    print("Error generating session:", e)
    exit(1)

# Step 4: Set token and test connection
kite.set_access_token(access_token)
profile = kite.profile()
print("Logged in as:", profile["user_name"])
