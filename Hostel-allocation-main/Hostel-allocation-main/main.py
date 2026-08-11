"""
CampusNest — FastAPI Backend
Combines: Rule-Based Engine + ML Model + Claude API
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import firebase_db as db, httpx, asyncio, json, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from ai_engine import AIMatchingEngine

app = FastAPI(
    title="CampusNest Backend",
    description="AI-powered hostel room allocation engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount current directory for static assets (CSS, Images, etc.)
# Note: In production, use a dedicated 'static' folder
app.mount("/static", StaticFiles(directory="."), name="static")

engine = AIMatchingEngine()

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class StudentProfile(BaseModel):
    name: str
    student_id: str
    branch: str
    semester: int
    gender: str
    preferences: List[str] = []
    room_type: str = "Double Sharing"
    preferred_block: Optional[str] = None
    preferred_floor: Optional[str] = None
    additional_requirements: Optional[str] = ""
    # New fields
    email: Optional[str] = None
    dob: Optional[str] = None
    blood_group: Optional[str] = None
    parent_phone: Optional[str] = None
    address: Optional[str] = None
    father_name: Optional[str] = None
    guardian_details: Optional[str] = None
    family_income: Optional[str] = None
    hometown: Optional[str] = None
    distance: Optional[str] = None
    scholarship: Optional[str] = None
    preferred_roommate: Optional[str] = None
    medical_issues: Optional[str] = None
    requirements: Optional[str] = None
    fee_receipt: Optional[str] = None
    fee_receipt_url: Optional[str] = None
    profile_picture: Optional[str] = None
    profile_picture_url: Optional[str] = None

class AllocationRequest(BaseModel):
    student: StudentProfile
    room_number: int

class RoomStatusUpdate(BaseModel):
    room_number: int
    status: str  # available | allocated | maintenance | partial

class AppStatusUpdate(BaseModel):
    status: str

class ComplaintModel(BaseModel):
    student_id: str
    category: str
    description: str

class ComplaintStatusUpdate(BaseModel):
    status: str

class LeaveRequestModel(BaseModel):
    student_id: str
    reason: str
    leaving_date: str
    return_date: str
    parent_contact: str

class RoomChangeRequestModel(BaseModel):
    student_id: str
    reason: str
    preferred_room: Optional[str] = None

class AnnouncementModel(BaseModel):
    title: str
    content: str
    target: str # 'all', 'students', 'staff'

class FeedbackModel(BaseModel):
    student_id: str
    rating: int
    comments: str

class RequestModel(BaseModel):
    student_id: str
    subject: str
    category: str
    description: str
    priority: str
    is_anonymous: bool = False

class RequestStatusUpdate(BaseModel):
    status: str
    warden_reply: Optional[str] = None

class FeeUpdateModel(BaseModel):
    total_fee: Optional[float] = None
    paid_amount: Optional[float] = None
    balance: Optional[float] = None
    due_date: Optional[str] = None
    extra_charges: Optional[list] = None

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main frontend HTML file"""
    return FileResponse("frontend_v3.html")


@app.get("/app")
async def serve_frontend():
    """Serve the main frontend HTML file"""
    return FileResponse("frontend_v3.html")


@app.get("/rooms")
def get_all_rooms():
    """Return all rooms with current status"""
    return {"rooms": db.get_all_rooms()}


@app.get("/rooms/available")
def get_available_rooms():
    """Return only available/partial rooms"""
    rooms = [r for r in db.get_all_rooms() if r["status"] in ("available", "partial")]
    return {"rooms": rooms, "count": len(rooms)}


@app.get("/stats")
def get_stats():
    """Dashboard statistics"""
    rooms = db.get_all_rooms()
    students = db.get_all_students()
    status_counts = {}
    for r in rooms:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    branch_counts = {}
    sem_counts = {}
    for s in students:
        branch_counts[s["branch"]] = branch_counts.get(s["branch"], 0) + 1
        sem_key = f"Sem {s['semester']}"
        sem_counts[sem_key] = sem_counts.get(sem_key, 0) + 1

    return {
        "total_rooms": len(rooms),
        "allocated": status_counts.get("allocated", 0),
        "available": status_counts.get("available", 0),
        "partial": status_counts.get("partial", 0),
        "maintenance": status_counts.get("maintenance", 0),
        "total_students": len(students),
        "by_branch": branch_counts,
        "by_semester": sem_counts,
    }


@app.post("/ai/recommend")
async def get_ai_recommendations(student: StudentProfile):
    """
    🧠 Main AI endpoint — runs all 3 engines in parallel:
    1. Rule-based scoring
    2. ML model prediction
    3. Claude API natural language recommendation
    Returns ranked room list + Claude's explanation
    """
    available_rooms = [r for r in db.get_all_rooms() if r["status"] in ("available", "partial")]

    if not available_rooms:
        raise HTTPException(status_code=404, detail="No available rooms found")

    # Run Rule-based + ML scoring (fast, synchronous)
    scored_rooms = engine.score_rooms(student.model_dump(), available_rooms)

    # Run Claude recommendation (async API call)
    top_5 = scored_rooms[:5]
    claude_explanation = await engine.get_claude_recommendation(student.model_dump(), top_5)

    return {
        "student": student.name,
        "top_recommendations": scored_rooms[:10],
        "best_match": scored_rooms[0] if scored_rooms else None,
        "ai_explanation": claude_explanation,
        "engines_used": ["rule_based", "ml_model", "claude_api"],
        "generated_at": datetime.now().isoformat()
    }


@app.post("/allocate")
def allocate_room(request: AllocationRequest):
    """Confirm room allocation for a student"""
    room = db.get_room(request.room_number)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if room["status"] == "allocated":
        raise HTTPException(status_code=400, detail="Room is already fully allocated")
    if room["status"] == "maintenance":
        raise HTTPException(status_code=400, detail="Room is under maintenance")

    db.allocate_room(request.room_number, request.student.model_dump())

    return {
        "success": True,
        "message": f"Room {request.room_number} allocated to {request.student.name}",
        "allocation_id": f"ALLOC-{request.room_number}-{request.student.student_id}",
        "room": db.get_room(request.room_number)
    }


@app.get("/students")
def get_students(branch: Optional[str] = None, semester: Optional[int] = None):
    """Get all students, optionally filtered"""
    students = db.get_all_students()
    if branch:
        students = [s for s in students if s["branch"].lower() == branch.lower()]
    if semester:
        students = [s for s in students if s["semester"] == semester]
    return {"students": students, "count": len(students)}


@app.put("/rooms/{room_number}/status")
def update_room_status(room_number: int, update: RoomStatusUpdate):
    """Update room status (maintenance, available, etc.)"""
    db.update_room_status(room_number, update.status)
    return {"success": True, "room": db.get_room(room_number)}


@app.post("/applications")
def submit_application(student: StudentProfile):
    """Student submits an online hostel application"""
    student_data = student.model_dump()
    student_data["status"] = "pending"
    db.add_student(student_data)
    return {"success": True, "message": "Application submitted successfully", "student_id": student.student_id}


@app.get("/applications/{student_id}")
def track_application(student_id: str):
    """Track application status for a student"""
    student = db.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Application not found")
    return student


@app.delete("/students/{student_id}")
def delete_student(student_id: str):
    """Admin removes a student and frees up their room"""
    success = db.remove_student(student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"success": True, "message": "Student removed and room updated"}


@app.put("/applications/{student_id}/status")
def update_application_status(student_id: str, update: AppStatusUpdate):
    """Admin rejects or updates an application status"""
    try:
        db.update_student_status(student_id, update.status)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/applications/{student_id}/accept")
def accept_offer(student_id: str):
    db.accept_room_offer(student_id)
    return {"success": True}

@app.post("/applications/{student_id}/reject")
def reject_offer(student_id: str):
    db.reject_room_offer(student_id)
    return {"success": True}

@app.post("/documents/upload/{student_id}")
async def upload_document(student_id: str, doc_type: str, file: UploadFile = File(...)):
    """Handle document uploads (admission letter, fee receipt, ID proof)"""
    allowed_types = ["admission_letter", "fee_receipt", "id_proof", "medical_certificate"]
    if doc_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"doc_type must be one of {allowed_types}")

    contents = await file.read()
    db.save_document(student_id, doc_type, file.filename)

    return {
        "success": True,
        "student_id": student_id,
        "doc_type": doc_type,
        "filename": file.filename,
        "size_kb": round(len(contents) / 1024, 1)
    }

@app.post("/complaints")
def create_complaint(complaint: ComplaintModel):
    comp_data = complaint.model_dump()
    comp_id = db.add_complaint(comp_data)
    return {"success": True, "complaint_id": comp_id}

@app.get("/complaints")
def get_complaints():
    return {"complaints": db.get_complaints()}

@app.put("/complaints/{complaint_id}/status")
def update_complaint(complaint_id: str, update: ComplaintStatusUpdate):
    db.update_complaint_status(complaint_id, update.status)
    return {"success": True}

@app.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: str):
    db.delete_complaint(complaint_id)
    return {"success": True}

@app.get("/documents/{student_id}")
def get_documents(student_id: str):
    """Get document status for a student"""
    docs = db.get_documents(student_id)
    required = ["admission_letter", "fee_receipt"]
    complete = all(d in docs for d in required)
    return {
        "student_id": student_id,
        "documents": docs,
        "complete": complete,
        "missing": [d for d in required if d not in docs]
    }

# ---------------- NEW FEATURE ROUTES ----------------

@app.get("/fees/{student_id}")
def get_fees(student_id: str):
    return db.get_student_fees(student_id)

@app.put("/fees/{student_id}")
def update_fees(student_id: str, fee_update: FeeUpdateModel):
    db.update_student_fees(student_id, fee_update.model_dump(exclude_unset=True))
    return {"success": True, "message": "Fees updated successfully"}

@app.post("/requests")
def create_request(req: RequestModel):
    req_id = db.add_student_request(req.model_dump())
    return {"success": True, "request_id": req_id}

@app.get("/requests")
def get_all_requests():
    return {"requests": db.get_all_requests()}

@app.get("/requests/{student_id}")
def get_student_requests(student_id: str):
    return {"requests": db.get_student_requests(student_id)}

@app.put("/requests/{req_id}/status")
def update_req_status(req_id: str, update: RequestStatusUpdate):
    db.update_request_status(req_id, update.status, update.warden_reply)
    return {"success": True}

@app.delete("/requests/{req_id}")
def delete_request(req_id: str):
    db.delete_request(req_id)
    return {"success": True}

@app.post("/leave-requests")
def create_leave_request(req: LeaveRequestModel):
    req_id = db.add_leave_request(req.model_dump())
    return {"success": True, "leave_id": req_id}

@app.get("/leave-requests")
def get_all_leave_requests(student_id: Optional[str] = None):
    return {"leave_requests": db.get_leave_requests(student_id)}

@app.put("/leave-requests/{leave_id}/status")
def update_leave_status(leave_id: str, update: AppStatusUpdate):
    db.update_leave_status(leave_id, update.status)
    return {"success": True}

@app.delete("/leave-requests/{leave_id}")
def delete_leave_request(leave_id: str):
    db.delete_leave_request(leave_id)
    return {"success": True}

@app.post("/room-change-requests")
def create_room_change_request(req: RoomChangeRequestModel):
    req_id = db.add_room_change_request(req.model_dump())
    return {"success": True, "request_id": req_id}

@app.get("/room-change-requests")
def get_room_change_requests(student_id: Optional[str] = None):
    return {"room_change_requests": db.get_room_change_requests(student_id)}

@app.put("/room-change-requests/{req_id}/status")
def update_room_change_status(req_id: str, update: AppStatusUpdate):
    db.update_room_change_status(req_id, update.status)
    return {"success": True}

@app.delete("/room-change-requests/{req_id}")
def delete_room_change_request(req_id: str):
    db.delete_room_change_request(req_id)
    return {"success": True}

@app.post("/announcements")
def create_announcement(ann: AnnouncementModel):
    ann_id = db.add_announcement(ann.model_dump())
    return {"success": True, "announcement_id": ann_id}

@app.get("/announcements")
def get_announcements():
    return {"announcements": db.get_announcements()}

@app.post("/feedback")
def submit_feedback(fb: FeedbackModel):
    fb_id = db.add_feedback(fb.model_dump())
    return {"success": True, "feedback_id": fb_id}

@app.get("/feedback")
def get_feedback():
    return {"feedbacks": db.get_feedbacks()}
