import firebase_admin, os
from firebase_admin import credentials, firestore

key_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-key.json")
cred = credentials.Certificate(key_path)  # your downloaded file
firebase_admin.initialize_app(cred)

db = firestore.client()