import httpx
import os
import dotenv

dotenv.load_dotenv()


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

EMAIL = "test@example.com"
PASSWORD = "testing123"

def get_token():
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
    }

    response = httpx.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("Login failed:", response.text)
        return None

    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    user = data.get("user", {})
    
    print("✅ Access Token:")
    print(access_token)
    print("🧑 User ID:", user.get("id"))
    return access_token


if __name__ == "__main__":
    get_token()
