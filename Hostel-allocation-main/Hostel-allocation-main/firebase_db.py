from firebase_config import db

# ---------------- ROOMS ----------------
def get_all_rooms():
    return [doc.to_dict() for doc in db.collection("rooms").stream()]

def get_room(room_number):
    doc = db.collection("rooms").document(str(room_number)).get()
    return doc.to_dict() if doc.exists else None

def add_room(room):
    db.collection("rooms").document(str(room["room_number"])).set(room)

def update_room_status(room_number, status):
    db.collection("rooms").document(str(room_number)).update({
        "status": status
    })

# ---------------- STUDENTS ----------------
def get_all_students():
    return [doc.to_dict() for doc in db.collection("students").stream()]

def get_student(student_id):
    doc = db.collection("students").document(student_id).get()
    return doc.to_dict() if doc.exists else None

def add_student(student):
    db.collection("students").document(student["student_id"]).set(student)

def update_student_status(student_id, status):
    db.collection("students").document(student_id).update({"status": status})

# ---------------- ALLOCATION ----------------
def allocate_room(room_number, student):
    room_ref = db.collection("rooms").document(str(room_number))
    room = room_ref.get().to_dict()

    occupants = room.get("occupants", [])
    occupants.append(student)

    status = "allocated" if len(occupants) >= room["capacity"] else "partial"

    room_ref.update({
        "occupants": occupants,
        "status": status
    })

    # save student
    db.collection("students").document(student["student_id"]).set({
        **student,
        "room": room_number,
        "status": "allocated"
    })

def accept_room_offer(student_id):
    db.collection("students").document(student_id).update({"status": "confirmed"})

def reject_room_offer(student_id):
    student_ref = db.collection("students").document(student_id)
    doc = student_ref.get()
    if not doc.exists: return
    student = doc.to_dict()
    if "room" in student and student["room"]:
        room_number = student["room"]
        room_ref = db.collection("rooms").document(str(room_number))
        room_doc = room_ref.get()
        if room_doc.exists:
            room = room_doc.to_dict()
            occupants = [o for o in room.get("occupants", []) if o.get("student_id") != student_id]
            status = "partial" if len(occupants) > 0 else "available"
            if room.get("status") == "maintenance": status = "maintenance"
            room_ref.update({"occupants": occupants, "status": status})
            
    student_ref.update({
        "status": "pending",
        "room": None
    })

# ---------------- DOCUMENTS ----------------
def save_document(student_id, doc_type, filename):
    db.collection("documents").document(student_id).set({
        doc_type: filename
    }, merge=True)

# ---------------- COMPLAINTS ----------------
import uuid

def add_complaint(complaint):
    complaint_id = str(uuid.uuid4())
    complaint["id"] = complaint_id
    complaint["status"] = "Open"
    db.collection("complaints").document(complaint_id).set(complaint)
    return complaint_id

def get_complaints():
    return [doc.to_dict() for doc in db.collection("complaints").stream()]

def update_complaint_status(complaint_id, status):
    db.collection("complaints").document(complaint_id).update({"status": status})

def delete_complaint(complaint_id):
    db.collection("complaints").document(complaint_id).delete()

def remove_student(student_id):
    student_ref = db.collection("students").document(student_id)
    doc = student_ref.get()
    if not doc.exists:
        return False
        
    student = doc.to_dict()
    
    if "room" in student and student["room"]:
        room_number = student["room"]
        room_ref = db.collection("rooms").document(str(room_number))
        room_doc = room_ref.get()
        if room_doc.exists:
            room = room_doc.to_dict()
            occupants = [o for o in room.get("occupants", []) if o.get("student_id") != student_id]
            status = "partial" if len(occupants) > 0 else "available"
            if room.get("status") == "maintenance":
                status = "maintenance"
            room_ref.update({"occupants": occupants, "status": status})
            
    student_ref.delete()
    return True

# ---------------- FEES ----------------
def get_student_fees(student_id):
    doc = db.collection("fees").document(student_id).get()
    if doc.exists:
        return doc.to_dict()
    return {
        "student_id": student_id,
        "total_fee": 50000,
        "paid_amount": 0,
        "balance": 50000,
        "due_date": "2026-12-31",
        "extra_charges": []
    }

def update_student_fees(student_id, fee_data):
    db.collection("fees").document(student_id).set(fee_data, merge=True)

# ---------------- REQUESTS ----------------
def add_student_request(request_data):
    req_id = str(uuid.uuid4())
    request_data["id"] = req_id
    request_data["status"] = "Pending"
    db.collection("requests").document(req_id).set(request_data)
    return req_id

def get_all_requests():
    return [doc.to_dict() for doc in db.collection("requests").stream()]

def get_student_requests(student_id):
    return [doc.to_dict() for doc in db.collection("requests").where("student_id", "==", student_id).stream()]

def update_request_status(req_id, status, warden_reply=None):
    update_data = {"status": status}
    if warden_reply:
        update_data["warden_reply"] = warden_reply
    db.collection("requests").document(req_id).update(update_data)

def delete_request(req_id):
    db.collection("requests").document(req_id).delete()

# ---------------- LEAVE REQUESTS ----------------
def add_leave_request(leave_data):
    leave_id = str(uuid.uuid4())
    leave_data["id"] = leave_id
    leave_data["status"] = "Pending"
    leave_data["created_at"] = leave_data.get("created_at", "2026-05-09")
    db.collection("leave_requests").document(leave_id).set(leave_data)
    return leave_id

def get_leave_requests(student_id=None):
    if student_id:
        return [doc.to_dict() for doc in db.collection("leave_requests").where("student_id", "==", student_id).stream()]
    return [doc.to_dict() for doc in db.collection("leave_requests").stream()]

def update_leave_status(leave_id, status):
    db.collection("leave_requests").document(leave_id).update({"status": status})

def delete_leave_request(leave_id):
    db.collection("leave_requests").document(leave_id).delete()

# ---------------- ROOM CHANGE REQUESTS ----------------
def add_room_change_request(request_data):
    req_id = str(uuid.uuid4())
    request_data["id"] = req_id
    request_data["status"] = "Pending"
    request_data["created_at"] = request_data.get("created_at", "2026-05-09")
    db.collection("room_change_requests").document(req_id).set(request_data)
    return req_id

def get_room_change_requests(student_id=None):
    if student_id:
        return [doc.to_dict() for doc in db.collection("room_change_requests").where("student_id", "==", student_id).stream()]
    return [doc.to_dict() for doc in db.collection("room_change_requests").stream()]

def update_room_change_status(req_id, status):
    db.collection("room_change_requests").document(req_id).update({"status": status})

def delete_room_change_request(req_id):
    db.collection("room_change_requests").document(req_id).delete()

# ---------------- ANNOUNCEMENTS ----------------
def add_announcement(announcement_data):
    ann_id = str(uuid.uuid4())
    announcement_data["id"] = ann_id
    announcement_data["created_at"] = announcement_data.get("created_at", "2026-05-09")
    db.collection("announcements").document(ann_id).set(announcement_data)
    return ann_id

def get_announcements():
    # In a real app we might order by created_at desc
    return [doc.to_dict() for doc in db.collection("announcements").stream()]

# ---------------- FEEDBACK ----------------
def add_feedback(feedback_data):
    fb_id = str(uuid.uuid4())
    feedback_data["id"] = fb_id
    feedback_data["created_at"] = feedback_data.get("created_at", "2026-05-09")
    db.collection("student_feedback").document(fb_id).set(feedback_data)
    return fb_id

def get_feedbacks():
    return [doc.to_dict() for doc in db.collection("student_feedback").stream()]