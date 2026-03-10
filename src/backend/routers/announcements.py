"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """
    Get all active announcements based on current date
    Public endpoint - no authentication required
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Query for announcements where:
    # - end_date is greater than or equal to current date
    # - start_date is null OR start_date is less than or equal to current date
    query = {
        "end_date": {"$gte": current_date},
        "$or": [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": {"$lte": current_date}}
        ]
    }
    
    announcements = []
    for announcement in announcements_collection.find(query).sort("created_at", -1):
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: str = Query(...)) -> List[Dict[str, Any]]:
    """
    Get all announcements for management purposes
    Requires teacher authentication
    """
    # Verify teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    announcements = []
    for announcement in announcements_collection.find().sort("created_at", -1):
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    end_date: str,
    start_date: str = None,
    teacher_username: str = Query(...)
) -> Dict[str, Any]:
    """
    Create a new announcement
    Requires teacher authentication
    """
    # Verify teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate dates
    try:
        datetime.strptime(end_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Create announcement document
    announcement = {
        "message": message,
        "start_date": start_date,
        "end_date": end_date,
        "created_by": teacher_username,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: str,
    end_date: str,
    start_date: str = None,
    teacher_username: str = Query(...)
) -> Dict[str, Any]:
    """
    Update an existing announcement
    Requires teacher authentication
    """
    # Verify teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    existing = announcements_collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Validate dates
    try:
        datetime.strptime(end_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Update announcement
    update_data = {
        "message": message,
        "start_date": start_date,
        "end_date": end_date
    }
    
    announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    # Get updated announcement
    updated = announcements_collection.find_one({"_id": obj_id})
    updated["_id"] = str(updated["_id"])
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: str = Query(...)
) -> Dict[str, str]:
    """
    Delete an announcement
    Requires teacher authentication
    """
    # Verify teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
