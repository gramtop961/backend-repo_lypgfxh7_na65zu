import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import create_document, get_documents, db
from schemas import Freelancer, PortfolioItem, Reservation, Advertisement, ForumThread, ForumPost

app = FastAPI(title="Designer Booking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Designer Booking Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ---------- Freelancers ----------
@app.post("/freelancers")
def create_freelancer(payload: Freelancer):
    inserted_id = create_document("freelancer", payload)
    return {"id": inserted_id}


@app.get("/freelancers")
def list_freelancers(skill: Optional[str] = Query(None, description="Filter by skill")):
    filt = {"skills": {"$regex": skill, "$options": "i"}} if skill else {}
    docs = get_documents("freelancer", filt, limit=None)
    # Convert ObjectId to string
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


# ---------- Portfolio ----------
@app.post("/portfolio")
def add_portfolio(item: PortfolioItem):
    # Ensure freelancer exists
    try:
        _id = ObjectId(item.freelancer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid freelancer_id")
    exists = db["freelancer"].find_one({"_id": _id})
    if not exists:
        raise HTTPException(status_code=404, detail="Freelancer not found")
    inserted_id = create_document("portfolioitem", item)
    return {"id": inserted_id}


@app.get("/portfolio")
def list_portfolio(freelancer_id: Optional[str] = None):
    filt = {"freelancer_id": freelancer_id} if freelancer_id else {}
    docs = get_documents("portfolioitem", filt, limit=None)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


# ---------- Reservations ----------
@app.post("/reservations")
def create_reservation(res: Reservation):
    # check overlap
    try:
        _id = ObjectId(res.freelancer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid freelancer_id")
    if not db["freelancer"].find_one({"_id": _id}):
        raise HTTPException(status_code=404, detail="Freelancer not found")

    # basic overlap check for same freelancer
    overlap = db["reservation"].find_one({
        "freelancer_id": res.freelancer_id,
        "$or": [
            {"start_time": {"$lt": res.end_time}, "end_time": {"$gt": res.start_time}},
        ]
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Reservation overlaps with an existing booking")

    inserted_id = create_document("reservation", res)
    return {"id": inserted_id}


@app.get("/reservations")
def list_reservations(freelancer_id: Optional[str] = None, business_email: Optional[str] = None):
    filt = {}
    if freelancer_id:
        filt["freelancer_id"] = freelancer_id
    if business_email:
        filt["business_email"] = business_email
    docs = get_documents("reservation", filt, limit=None)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


# ---------- Advertisements ----------
@app.post("/ads")
def create_ad(ad: Advertisement):
    if ad.ad_type == "business":
        if not ad.designers or len(ad.designers) == 0:
            raise HTTPException(status_code=400, detail="Business ads must include designers responsible")
        # Ensure heading includes each designer name (case-insensitive contains)
        heading_lower = ad.heading.lower()
        missing = [n for n in ad.designers if n.lower() not in heading_lower]
        if missing:
            raise HTTPException(status_code=400, detail=f"Heading must include designers: {', '.join(missing)}")
    inserted_id = create_document("advertisement", ad)
    return {"id": inserted_id}


@app.get("/ads")
def list_ads(ad_type: Optional[str] = None):
    filt = {"ad_type": ad_type} if ad_type else {}
    docs = get_documents("advertisement", filt, limit=50)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


# ---------- Forum ----------
@app.post("/forum/threads")
def create_thread(thread: ForumThread):
    inserted_id = create_document("forumthread", thread)
    return {"id": inserted_id}


@app.get("/forum/threads")
def list_threads(tag: Optional[str] = None):
    filt = {"tags": {"$regex": tag, "$options": "i"}} if tag else {}
    docs = get_documents("forumthread", filt, limit=50)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


@app.post("/forum/posts")
def create_post(post: ForumPost):
    # ensure thread exists
    try:
        _id = ObjectId(post.thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread_id")
    if not db["forumthread"].find_one({"_id": _id}):
        raise HTTPException(status_code=404, detail="Thread not found")
    inserted_id = create_document("forumpost", post)
    return {"id": inserted_id}


@app.get("/forum/posts")
def list_posts(thread_id: str):
    docs = get_documents("forumpost", {"thread_id": thread_id}, limit=200)
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return {"items": docs}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
