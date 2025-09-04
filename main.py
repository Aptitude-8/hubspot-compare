from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api.hubspot_client import HubSpotClient
from api.models import TokenPair
from api.comparison import PropertyComparer
import logging
import time
from typing import Dict, Any
import hashlib
import secrets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HubSpot Property Comparison Tool", version="1.0.0")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Session configuration
SESSION_TIMEOUT = 3600  # 1 hour in seconds
CLEANUP_INTERVAL = 300  # Clean up expired sessions every 5 minutes
CACHE_TIMEOUT = 900  # 15 minutes cache timeout for properties

# In-memory storage for session data with timestamps
session_data: Dict[str, Dict[str, Any]] = {}
last_cleanup = time.time()

def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    global last_cleanup
    current_time = time.time()
    
    if current_time - last_cleanup < CLEANUP_INTERVAL:
        return
    
    expired_sessions = []
    for session_id, data in session_data.items():
        if current_time - data.get("last_accessed", 0) > SESSION_TIMEOUT:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_data[session_id]
        logger.info(f"Cleaned up expired session: {session_id}")
    
    last_cleanup = current_time

def generate_session_id() -> str:
    """Generate a secure session ID"""
    return hashlib.sha256(f"{secrets.token_hex(16)}{time.time()}".encode()).hexdigest()[:32]

def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data and update last accessed time"""
    cleanup_expired_sessions()
    
    if session_id not in session_data:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session_data[session_id]["last_accessed"] = time.time()
    return session_data[session_id]

def create_session(client_a: HubSpotClient, client_b: HubSpotClient, portal_a_token: str, portal_b_token: str, portal_a_name: str = "Portal A", portal_b_name: str = "Portal B") -> str:
    """Create a new session with clients and tokens"""
    session_id = generate_session_id()
    current_time = time.time()
    
    session_data[session_id] = {
        "client_a": client_a,
        "client_b": client_b,
        "portal_a_token": portal_a_token,
        "portal_b_token": portal_b_token,
        "portal_a_name": portal_a_name,
        "portal_b_name": portal_b_name,
        "created_at": current_time,
        "last_accessed": current_time,
        "cache": {
            "objects": {
                "data": None,
                "timestamp": None
            },
            "properties": {}  # Will store by object_type
        }
    }
    
    logger.info(f"Created new session: {session_id} ({portal_a_name} vs {portal_b_name})")
    return session_id

def is_cache_valid(timestamp: float) -> bool:
    """Check if cached data is still valid"""
    if timestamp is None:
        return False
    return time.time() - timestamp < CACHE_TIMEOUT

def clear_session_cache(session_id: str, object_type: str = None):
    """Clear cache for a session, optionally for specific object type"""
    if session_id not in session_data:
        return
    
    session = session_data[session_id]
    if object_type:
        # Clear specific object type cache
        if object_type in session["cache"]["properties"]:
            del session["cache"]["properties"][object_type]
            logger.info(f"Cleared cache for {object_type} in session {session_id}")
    else:
        # Clear all cache
        session["cache"] = {
            "objects": {"data": None, "timestamp": None},
            "properties": {}
        }
        logger.info(f"Cleared all cache for session {session_id}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Check if there's an active session from cookie or query param
    session_id = request.query_params.get("session_id")
    existing_session = None
    
    if session_id:
        try:
            existing_session = get_session(session_id)
        except HTTPException:
            existing_session = None
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "existing_session": existing_session,
        "session_id": session_id if existing_session else None
    })

@app.post("/validate-tokens")
async def validate_tokens(
    request: Request,
    portal_a_name: str = Form(...),
    portal_a_token: str = Form(...),
    portal_b_name: str = Form(...),
    portal_b_token: str = Form(...)
):
    try:
        client_a = HubSpotClient(portal_a_token)
        client_b = HubSpotClient(portal_b_token)
        
        # Validate tokens by making test requests
        await client_a.validate_token()
        await client_b.validate_token()
        
        # Create new session with secure ID and portal names
        session_id = create_session(client_a, client_b, portal_a_token, portal_b_token, portal_a_name, portal_b_name)
        
        return {"success": True, "session_id": session_id, "message": "Tokens validated successfully"}
    
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Token validation failed: {str(e)}")

@app.get("/objects/{session_id}")
async def get_objects(session_id: str):
    try:
        session = get_session(session_id)
        
        # Check cache first
        objects_cache = session["cache"]["objects"]
        if is_cache_valid(objects_cache["timestamp"]) and objects_cache["data"]:
            logger.info(f"Using cached objects for session {session_id}")
            return objects_cache["data"]
        
        # Cache miss - fetch fresh data
        client_a = session["client_a"]
        client_b = session["client_b"]
        
        logger.info(f"Fetching fresh objects data for session {session_id}")
        objects_a = await client_a.get_available_objects()
        objects_b = await client_b.get_available_objects()
        
        result = {
            "portal_a": objects_a,
            "portal_b": objects_b
        }
        
        # Debug logging for custom objects
        logger.info(f"Portal A custom objects count: {len(objects_a.get('custom', []))}")
        logger.info(f"Portal B custom objects count: {len(objects_b.get('custom', []))}")
        for obj in objects_a.get('custom', []):
            logger.info(f"Portal A custom object: {obj.name} (ID: {obj.objectTypeId})")
        for obj in objects_b.get('custom', []):
            logger.info(f"Portal B custom object: {obj.name} (ID: {obj.objectTypeId})")
        
        # Update cache
        session["cache"]["objects"] = {
            "data": result,
            "timestamp": time.time()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get objects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get objects: {str(e)}")

@app.get("/properties/{session_id}/{object_type}")
async def get_properties(session_id: str, object_type: str):
    try:
        session = get_session(session_id)
        
        # Check cache first
        properties_cache = session["cache"]["properties"].get(object_type)
        if properties_cache and is_cache_valid(properties_cache["timestamp"]):
            logger.info(f"Using cached properties for {object_type} in session {session_id}")
            return properties_cache["data"]
        
        # Cache miss - fetch fresh data
        client_a = session["client_a"]
        client_b = session["client_b"]
        
        logger.info(f"Fetching fresh properties for {object_type} in session {session_id}")
        properties_a = await client_a.get_properties(object_type)
        properties_b = await client_b.get_properties(object_type)
        
        result = {
            "portal_a": properties_a,
            "portal_b": properties_b,
            "object_type": object_type
        }
        
        # Update cache
        session["cache"]["properties"][object_type] = {
            "data": result,
            "timestamp": time.time()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get properties: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get properties: {str(e)}")

@app.post("/refresh-cache/{session_id}")
async def refresh_cache(session_id: str, request: Request):
    """Refresh cache for a session, optionally for specific object type"""
    try:
        session = get_session(session_id)
        object_type = request.query_params.get("object_type")
        
        clear_session_cache(session_id, object_type)
        
        if object_type:
            return {"success": True, "message": f"Cache refreshed for {object_type}"}
        else:
            return {"success": True, "message": "All cache refreshed"}
    
    except Exception as e:
        logger.error(f"Failed to refresh cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh cache: {str(e)}")

@app.get("/cache-status/{session_id}")
async def get_cache_status(session_id: str):
    """Get cache status for a session"""
    try:
        session = get_session(session_id)
        cache = session["cache"]
        current_time = time.time()
        
        status = {
            "objects": {
                "cached": cache["objects"]["data"] is not None,
                "valid": is_cache_valid(cache["objects"]["timestamp"]),
                "age_seconds": current_time - cache["objects"]["timestamp"] if cache["objects"]["timestamp"] else None
            },
            "properties": {}
        }
        
        for obj_type, prop_cache in cache["properties"].items():
            status["properties"][obj_type] = {
                "cached": True,
                "valid": is_cache_valid(prop_cache["timestamp"]),
                "age_seconds": current_time - prop_cache["timestamp"]
            }
        
        return status
    
    except Exception as e:
        logger.error(f"Failed to get cache status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache status: {str(e)}")

@app.get("/custom-object-matching/{session_id}")
async def custom_object_matching(request: Request, session_id: str):
    """Show custom object matching interface"""
    session = get_session(session_id)
    objects_data = await get_objects(session_id)
    
    portal_a_objects = objects_data["portal_a"].get("custom", [])
    portal_b_objects = objects_data["portal_b"].get("custom", [])
    
    # Objects that exist only in Portal B (for display)
    portal_a_ids = {obj.objectTypeId for obj in portal_a_objects}
    portal_b_only = [obj for obj in portal_b_objects if obj.objectTypeId not in portal_a_ids]
    
    return templates.TemplateResponse("custom_object_matching.html", {
        "request": request,
        "session_id": session_id,
        "portal_a_name": session.get("portal_a_name", "Portal A"),
        "portal_b_name": session.get("portal_b_name", "Portal B"),
        "portal_a_objects": portal_a_objects,
        "portal_b_objects": portal_b_objects,
        "portal_b_only_objects": portal_b_only
    })

@app.get("/compare-custom/{session_id}/{portal_a_id}/{portal_b_id}")
async def compare_custom_objects(request: Request, session_id: str, portal_a_id: str, portal_b_id: str):
    """Compare properties between matched custom objects"""
    try:
        session = get_session(session_id)
        client_a = session["client_a"]
        client_b = session["client_b"]
        
        # Get properties for both custom objects
        properties_a = await client_a.get_properties(portal_a_id)
        properties_b = await client_b.get_properties(portal_b_id)
        
        # Compare properties
        comparer = PropertyComparer()
        comparison_result = comparer.compare_properties(properties_a, properties_b)
        comparison_result.object_type = f"Custom Object ({portal_a_id} vs {portal_b_id})"
        
        return templates.TemplateResponse("comparison.html", {
            "request": request,
            "session_id": session_id,
            "object_type": comparison_result.object_type,
            "comparison": comparison_result,
            "portal_a_name": session.get("portal_a_name", "Portal A"),
            "portal_b_name": session.get("portal_b_name", "Portal B")
        })
        
    except Exception as e:
        logger.error(f"Failed to compare custom objects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare properties: {str(e)}")

@app.get("/compare/{session_id}/{object_type}", response_class=HTMLResponse)
async def compare_properties(request: Request, session_id: str, object_type: str):
    try:
        session = get_session(session_id)
        client_a = session["client_a"]
        client_b = session["client_b"]
        portal_a_name = session.get("portal_a_name", "Portal A")
        portal_b_name = session.get("portal_b_name", "Portal B")
        
        properties_a = await client_a.get_properties(object_type)
        properties_b = await client_b.get_properties(object_type)
        
        comparer = PropertyComparer()
        comparison_result = comparer.compare_properties(properties_a, properties_b)
        comparison_result.object_type = object_type
        
        return templates.TemplateResponse("comparison.html", {
            "request": request,
            "comparison": comparison_result,
            "object_type": object_type,
            "session_id": session_id,
            "portal_a_name": portal_a_name,
            "portal_b_name": portal_b_name
        })
    
    except Exception as e:
        logger.error(f"Failed to compare properties: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare properties: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)