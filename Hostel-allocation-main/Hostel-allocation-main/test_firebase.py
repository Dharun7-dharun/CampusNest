from dotenv import load_dotenv
load_dotenv()
from firebase_config import db
try:
    rooms = list(db.collection("rooms").limit(1).stream())
    print(f"Firebase connected! Found {len(rooms)} rooms.")
except Exception as e:
    print(f"Firebase connection failed: {e}")
