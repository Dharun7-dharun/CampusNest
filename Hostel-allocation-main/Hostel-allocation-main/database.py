import uuid
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL: Switch this to "mysql+pymysql://user:password@localhost/hostel" for MySQL
SQLALCHEMY_DATABASE_URL = "sqlite:///./hostel.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------------- MODELS ----------------

class Room(Base):
    __tablename__ = "rooms"
    room_number = Column(Integer, primary_key=True, index=True)
    capacity = Column(Integer)
    type = Column(String)
    status = Column(String)
    occupants = Column(JSON, default=list)

class Student(Base):
    __tablename__ = "students"
    student_id = Column(String, primary_key=True, index=True)
    name = Column(String)
    branch = Column(String)
    semester = Column(Integer)
    gender = Column(String)
    preferences = Column(JSON, default=list)
    room_type = Column(String)
    status = Column(String, default="pending")
    room = Column(Integer, nullable=True)
    
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    parent_phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    father_name = Column(String, nullable=True)
    guardian_details = Column(String, nullable=True)
    family_income = Column(String, nullable=True)
    hometown = Column(String, nullable=True)
    distance = Column(String, nullable=True)
    scholarship = Column(String, nullable=True)
    medical_issues = Column(String, nullable=True)
    
    fee_receipt = Column(String, nullable=True)
    fee_receipt_url = Column(Text, nullable=True)
    profile_picture = Column(String, nullable=True)
    profile_picture_url = Column(Text, nullable=True)

class Fee(Base):
    __tablename__ = "fees"
    student_id = Column(String, primary_key=True, index=True)
    total_fee = Column(Float, default=50000)
    paid_amount = Column(Float, default=0)
    balance = Column(Float, default=50000)
    due_date = Column(String, default="2026-12-31")
    extra_charges = Column(JSON, default=list)

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(String, primary_key=True, index=True)
    student_id = Column(String)
    category = Column(String)
    description = Column(Text)
    status = Column(String, default="Open")

class Request(Base):
    __tablename__ = "requests"
    id = Column(String, primary_key=True, index=True)
    student_id = Column(String)
    subject = Column(String)
    category = Column(String)
    description = Column(Text)
    priority = Column(String)
    is_anonymous = Column(Boolean, default=False)
    status = Column(String, default="Pending")
    warden_reply = Column(Text, nullable=True)

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(String, primary_key=True, index=True)
    student_id = Column(String)
    reason = Column(String)
    leaving_date = Column(String)
    return_date = Column(String)
    parent_contact = Column(String)
    status = Column(String, default="Pending")
    created_at = Column(String, default="2026-05-09")

class RoomChangeRequest(Base):
    __tablename__ = "room_change_requests"
    id = Column(String, primary_key=True, index=True)
    student_id = Column(String)
    reason = Column(String)
    preferred_room = Column(String, nullable=True)
    status = Column(String, default="Pending")
    created_at = Column(String, default="2026-05-09")

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    content = Column(Text)
    target = Column(String)
    created_at = Column(String, default="2026-05-09")

class Feedback(Base):
    __tablename__ = "student_feedback"
    id = Column(String, primary_key=True, index=True)
    student_id = Column(String)
    rating = Column(Integer)
    comments = Column(Text)
    created_at = Column(String, default="2026-05-09")

# Create all tables in DB
Base.metadata.create_all(bind=engine)

# ---------------- HELPER TO CONVERT SQLALCHEMY OBJS TO DICT ----------------
def to_dict(obj):
    if not obj: return None
    res = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    # JSON columns might need default handling if null
    return res

def to_dict_list(objs):
    return [to_dict(o) for o in objs]

# ---------------- ROOMS ----------------
def get_all_rooms():
    with SessionLocal() as db:
        return to_dict_list(db.query(Room).all())

def get_room(room_number):
    with SessionLocal() as db:
        return to_dict(db.query(Room).filter(Room.room_number == int(room_number)).first())

def add_room(room_data):
    with SessionLocal() as db:
        room = Room(**room_data)
        db.merge(room)
        db.commit()

def update_room_status(room_number, status):
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.room_number == int(room_number)).first()
        if room:
            room.status = status
            db.commit()

# ---------------- STUDENTS ----------------
def get_all_students():
    with SessionLocal() as db:
        return to_dict_list(db.query(Student).all())

def get_student(student_id):
    with SessionLocal() as db:
        return to_dict(db.query(Student).filter(Student.student_id == student_id).first())

def add_student(student_data):
    with SessionLocal() as db:
        student = Student(**student_data)
        db.merge(student)
        db.commit()

def update_student_status(student_id, status):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            student.status = status
            db.commit()

# ---------------- ALLOCATION ----------------
def allocate_room(room_number, student_data):
    with SessionLocal() as db:
        room = db.query(Room).filter(Room.room_number == int(room_number)).first()
        student = db.query(Student).filter(Student.student_id == student_data["student_id"]).first()
        
        if room and student:
            occupants = list(room.occupants) if room.occupants else []
            occupants.append(student_data)
            
            room.occupants = occupants
            room.status = "allocated" if len(occupants) >= room.capacity else "partial"
            
            student.room = int(room_number)
            student.status = "allocated"
            db.commit()

def accept_room_offer(student_id):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if student:
            student.status = "confirmed"
            db.commit()

def reject_room_offer(student_id):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student: return
        
        if student.room:
            room = db.query(Room).filter(Room.room_number == int(student.room)).first()
            if room:
                occupants = [o for o in (room.occupants or []) if o.get("student_id") != student_id]
                status = "partial" if len(occupants) > 0 else "available"
                if room.status == "maintenance": status = "maintenance"
                room.occupants = occupants
                room.status = status
                
        student.status = "pending"
        student.room = None
        db.commit()

def remove_student(student_id):
    with SessionLocal() as db:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student: return False
        
        if student.room:
            room = db.query(Room).filter(Room.room_number == int(student.room)).first()
            if room:
                occupants = [o for o in (room.occupants or []) if o.get("student_id") != student_id]
                status = "partial" if len(occupants) > 0 else "available"
                if room.status == "maintenance": status = "maintenance"
                room.occupants = occupants
                room.status = status
                
        db.delete(student)
        db.commit()
        return True

# ---------------- FEES ----------------
def get_student_fees(student_id):
    with SessionLocal() as db:
        fee = db.query(Fee).filter(Fee.student_id == student_id).first()
        if fee:
            return to_dict(fee)
        return {
            "student_id": student_id,
            "total_fee": 50000,
            "paid_amount": 0,
            "balance": 50000,
            "due_date": "2026-12-31",
            "extra_charges": []
        }

def update_student_fees(student_id, fee_data):
    with SessionLocal() as db:
        fee = db.query(Fee).filter(Fee.student_id == student_id).first()
        if fee:
            for k, v in fee_data.items():
                setattr(fee, k, v)
        else:
            fee = Fee(student_id=student_id, **fee_data)
            db.add(fee)
        db.commit()

# ---------------- COMPLAINTS ----------------
def add_complaint(complaint_data):
    with SessionLocal() as db:
        cid = str(uuid.uuid4())
        complaint_data["id"] = cid
        complaint_data["status"] = "Open"
        db.add(Complaint(**complaint_data))
        db.commit()
        return cid

def get_complaints():
    with SessionLocal() as db:
        return to_dict_list(db.query(Complaint).all())

def update_complaint_status(complaint_id, status):
    with SessionLocal() as db:
        comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if comp:
            comp.status = status
            db.commit()

def delete_complaint(complaint_id):
    with SessionLocal() as db:
        db.query(Complaint).filter(Complaint.id == complaint_id).delete()
        db.commit()

# ---------------- REQUESTS ----------------
def add_student_request(request_data):
    with SessionLocal() as db:
        rid = str(uuid.uuid4())
        request_data["id"] = rid
        request_data["status"] = "Pending"
        db.add(Request(**request_data))
        db.commit()
        return rid

def get_all_requests():
    with SessionLocal() as db:
        return to_dict_list(db.query(Request).all())

def get_student_requests(student_id):
    with SessionLocal() as db:
        return to_dict_list(db.query(Request).filter(Request.student_id == student_id).all())

def update_request_status(req_id, status, warden_reply=None):
    with SessionLocal() as db:
        req = db.query(Request).filter(Request.id == req_id).first()
        if req:
            req.status = status
            if warden_reply:
                req.warden_reply = warden_reply
            db.commit()

def delete_request(req_id):
    with SessionLocal() as db:
        db.query(Request).filter(Request.id == req_id).delete()
        db.commit()

# ---------------- LEAVE REQUESTS ----------------
def add_leave_request(leave_data):
    with SessionLocal() as db:
        lid = str(uuid.uuid4())
        leave_data["id"] = lid
        leave_data["status"] = "Pending"
        leave_data["created_at"] = leave_data.get("created_at", "2026-05-09")
        db.add(LeaveRequest(**leave_data))
        db.commit()
        return lid

def get_leave_requests(student_id=None):
    with SessionLocal() as db:
        if student_id:
            return to_dict_list(db.query(LeaveRequest).filter(LeaveRequest.student_id == student_id).all())
        return to_dict_list(db.query(LeaveRequest).all())

def update_leave_status(leave_id, status):
    with SessionLocal() as db:
        leave = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
        if leave:
            leave.status = status
            db.commit()

def delete_leave_request(leave_id):
    with SessionLocal() as db:
        db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).delete()
        db.commit()

# ---------------- ROOM CHANGE REQUESTS ----------------
def add_room_change_request(request_data):
    with SessionLocal() as db:
        rid = str(uuid.uuid4())
        request_data["id"] = rid
        request_data["status"] = "Pending"
        request_data["created_at"] = request_data.get("created_at", "2026-05-09")
        db.add(RoomChangeRequest(**request_data))
        db.commit()
        return rid

def get_room_change_requests(student_id=None):
    with SessionLocal() as db:
        if student_id:
            return to_dict_list(db.query(RoomChangeRequest).filter(RoomChangeRequest.student_id == student_id).all())
        return to_dict_list(db.query(RoomChangeRequest).all())

def update_room_change_status(req_id, status):
    with SessionLocal() as db:
        req = db.query(RoomChangeRequest).filter(RoomChangeRequest.id == req_id).first()
        if req:
            req.status = status
            db.commit()

def delete_room_change_request(req_id):
    with SessionLocal() as db:
        db.query(RoomChangeRequest).filter(RoomChangeRequest.id == req_id).delete()
        db.commit()

# ---------------- ANNOUNCEMENTS ----------------
def add_announcement(announcement_data):
    with SessionLocal() as db:
        aid = str(uuid.uuid4())
        announcement_data["id"] = aid
        announcement_data["created_at"] = announcement_data.get("created_at", "2026-05-09")
        db.add(Announcement(**announcement_data))
        db.commit()
        return aid

def get_announcements():
    with SessionLocal() as db:
        return to_dict_list(db.query(Announcement).all())

# ---------------- FEEDBACK ----------------
def add_feedback(feedback_data):
    with SessionLocal() as db:
        fid = str(uuid.uuid4())
        feedback_data["id"] = fid
        feedback_data["created_at"] = feedback_data.get("created_at", "2026-05-09")
        db.add(Feedback(**feedback_data))
        db.commit()
        return fid

def get_feedbacks():
    with SessionLocal() as db:
        return to_dict_list(db.query(Feedback).all())