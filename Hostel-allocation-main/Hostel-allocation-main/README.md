# HostelAI — Backend Setup Guide

## 🏗️ Project Structure
```
hostel-ai-backend/
├── main.py          ← FastAPI app & all routes
├── ai_engine.py     ← 3-layer AI matching engine
├── database.py      ← In-memory DB with seed data
├── requirements.txt ← Python dependencies
├── frontend_v3.html  ← Redesigned Premium Frontend
└── .env             ← Your API keys (create this)
```

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
Create a `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Then load it before running:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Start the backend
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open the frontend
Open `frontend_v3.html` in your browser.
The green dot in the header means the backend is connected ✅

---

## 🤖 How the AI Works (3 Layers)

### Layer 1 — Rule-Based Scoring (60% weight)
Fast, transparent scoring based on:
- Room capacity vs student's preference
- Branch & semester match with existing roommates
- Shared lifestyle preferences (non-smoker, early riser, etc.)
- Block/floor preference match
- Penalties for full/maintenance rooms

### Layer 2 — ML Model (40% weight)
A Random Forest classifier trained on synthetic historical data.
- 9 input features (branch similarity, semester diff, shared prefs, etc.)
- Outputs compatibility probability 0.0–1.0
- In production: replace synthetic data with your real allocation records

### Layer 3 — Claude AI (Natural Language Explanation)
Called once per recommendation request.
- Receives top 3 rooms + student profile
- Returns a human-readable explanation of WHY the top room is best
- Requires `ANTHROPIC_API_KEY` in environment

**Final Score = 0.6 × Rule Score + 0.4 × ML Score**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/stats` | Dashboard statistics |
| GET | `/rooms` | All rooms |
| GET | `/rooms/available` | Available rooms only |
| POST | `/ai/recommend` | **Main AI endpoint** — returns ranked rooms + Claude explanation |
| POST | `/allocate` | Confirm room allocation |
| GET | `/students` | Student list (with filters) |
| PUT | `/rooms/{num}/status` | Update room status |
| POST | `/documents/upload/{id}` | Upload student document |
| GET | `/documents/{id}` | Check document status |

### Example: AI Recommend Request
```json
POST /ai/recommend
{
  "name": "Aarav Sharma",
  "student_id": "22CS1045",
  "branch": "CS",
  "semester": 3,
  "gender": "Male",
  "preferences": ["Non-smoker", "Quiet Study", "Early Riser"],
  "room_type": "Double Sharing",
  "preferred_block": "Block A",
  "preferred_floor": "2nd Floor",
  "additional_requirements": "Near library"
}
```

### Example Response
```json
{
  "student": "Aarav Sharma",
  "best_match": {
    "room_number": 204,
    "block": "Block A",
    "combined_score": 87.4,
    "rule_score": 82.0,
    "ml_score": 79.2,
    "match_reasons": ["Same Branch (CS)", "Quiet Study", "Non-smoker"]
  },
  "top_recommendations": [...],
  "ai_explanation": "Room 204 in Block A is the best match for Aarav...",
  "engines_used": ["rule_based", "ml_model", "claude_api"]
}
```

---

## 🗄️ Production Upgrade Path

| Feature | Dev (current) | Production |
|---------|--------------|------------|
| Database | In-memory Python dict | PostgreSQL / MongoDB |
| File storage | Local memory | AWS S3 / Cloudinary |
| ML model | Synthetic training data | Train on real hostel records |
| Auth | None | JWT tokens |
| Deployment | localhost | Render / Railway / AWS EC2 |

---

## 📚 Interactive API Docs
When backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
