from dotenv import load_dotenv
load_dotenv()
from firebase_db import add_room

for i in range(101, 111):
    room = {
        "room_number": i,
        "block": "A",
        "floor": 1,
        "capacity": 2,
        "status": "available",
        "occupants": []
    }
    add_room(room)

print("Rooms added to Firebase")