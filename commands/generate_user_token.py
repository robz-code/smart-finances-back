import httpx
import os
import dotenv
import clipboard
import sys

dotenv.load_dotenv()


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Remove hardcoded EMAIL and PASSWORD
# EMAIL = "test@example.com"
# PASSWORD = "testing123"

def get_token(email, password):
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "email": email,
        "password": password,
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
    clipboard.copy(access_token)
    print(access_token)
    print("El acces token se ha copiado para el 🧑 User ID:", user.get("id"))
    return access_token


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_user_token.py <email> <password>")
        sys.exit(1)
    email = sys.argv[1]
    password = sys.argv[2]
    get_token(email, password)
