from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime
import uuid
import json
from .database import init_db, SessionLocal, Conversation, ChatHistory, get_recent_history
from .memory import add_to_ltm, query_ltm
from .tools import search_internet

# --- App Initialization ---
app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

# Mount static files (CSS/JS)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    api_key: str
    model: str
    user_id: str
    conversation_id: str
    use_search: bool = False

class NewConvRequest(BaseModel):
    user_id: str

# --- Routes ---

# 1. Serve Frontend HTML
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html") as f:
        return f.read()

# 2. Create New Conversation
@app.post("/api/conversations/new")
async def new_conversation(req: NewConvRequest):
    if req.user_id == "Guest":
        return {"conversation_id": "guest-session-" + str(uuid.uuid4())}
        
    db = SessionLocal()
    conv_id = str(uuid.uuid4())
    new_conv = Conversation(id=conv_id, user_id=req.user_id, title="New Chat")
    db.add(new_conv)
    db.commit()
    db.close()
    return {"conversation_id": conv_id}

# 3. List Conversations
@app.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str):
    if user_id == "Guest":
        return []
    
    db = SessionLocal()
    convs = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()
    result = [{"id": c.id, "title": c.title} for c in convs]
    db.close()
    return result

# 4. Get History
@app.get("/api/history/{conversation_id}")
async def get_history(conversation_id: str):
    if "guest-session" in conversation_id:
        return []

    db = SessionLocal()
    msgs = db.query(ChatHistory).filter(ChatHistory.conversation_id == conversation_id).order_by(ChatHistory.timestamp).all()
    result = [{"role": m.role, "content": m.content} for m in msgs]
    db.close()
    return result

# --- Agent Logic Functions ---

def agent_reason(client, model, user_query, chat_history):
    """
    Asks the LLM to decide if a search is needed.
    Returns: (needs_search: bool, search_query: str)
    """
    system_prompt = """
    You are an AI Decision Engine. Your job is to decide if the user's query requires an internet search.
    
    Rules:
    1. If the query asks for current news, weather, specific latest data, or time-sensitive info, you MUST search.
    2. If the query is about general knowledge, math, coding, or casual chat, do NOT search.
    3. Respond ONLY with valid JSON in this format: {"needs_search": boolean, "query": "search term if true"}
    
    Examples:
    User: "What is the capital of France?" -> {"needs_search": false, "query": ""}
    User: "Who won the game last night?" -> {"needs_search": true, "query": "sports game results last night"}
    User: "What is the time now?" -> {"needs_search": true, "query": "current time"}
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history[-3:]) 
    messages.append({"role": "user", "content": user_query})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        
        content = response.choices[0].message.content
        
        # Clean up markdown code blocks if present
        if "```json" in content: content = content.split("```json")[1].split("```")[0]
        elif "```" in content: content = content.split("```")[1].split("```")[0]
        
        decision = json.loads(content.strip())
        return decision.get("needs_search", False), decision.get("query", user_query)
        
    except Exception as e:
        print(f"[AGENT REASONING ERROR] {e}")
        return False, ""

# 5. Chat Endpoint
@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.api_key:
        raise HTTPException(status_code=400, detail="API Key is required")

    db = SessionLocal()
    is_guest = (req.user_id == "Guest")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=req.api_key)

    # 1. Retrieve Memory
    ltm_context = []
    if not is_guest:
        ltm_context = query_ltm(req.message, req.user_id)
    
    stm_history = []
    if not is_guest and "guest-session" not in req.conversation_id:
        stm_history = get_recent_history(db, req.conversation_id, limit=6)

    # 2. DECISION LOGIC (IMPROVED)
    needs_search = False
    search_query = req.message
    
    # A. SAFETY NET: Hardcoded Keywords (Guaranteed Trigger)
    search_keywords = ["latest", "news", "current", "today", "weather", "time", "live", "recent", "update"]
    if any(keyword in req.message.lower() for keyword in search_keywords):
        needs_search = True
        search_query = req.message
        print(f"[AGENT] Keyword detected. Forcing Search.")
    
    # B. LLM DECISION: Only if keywords not found and search is enabled
    elif req.use_search:
        print("[AGENT] Thinking: Do I need to search?")
        needs_search, search_query = agent_reason(client, req.model, req.message, stm_history)
        print(f"[AGENT] Decision: Search={needs_search}, Query='{search_query}'")

    # 3. EXECUTE TOOLS
    search_context = ""
    if needs_search:
        print(f"[AGENT] Executing Search: {search_query}")
        search_context = search_internet(search_query)
        if not search_context:
            search_context = "Search completed but found no relevant results."

    # 4. FINAL RESPONSE GENERATION
    system_content = (
        "You are a helpful AI Agent.\n"
        f"Current System Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )

    if ltm_context:
        system_content += "### User Memories:\n" + "\n".join(ltm_context) + "\n\n"

    if search_context:
        system_content += (
            "### CRITICAL: LIVE INTERNET SEARCH RESULTS\n"
            "I have performed a real-time search for you. The results are below.\n"
            "You MUST use these results to answer the user's question.\n"
            "DO NOT say 'I don't have internet access' or 'I cannot browse'.\n"
            "DO NOT use your training data for time-sensitive facts if search results are present.\n\n"
            f"SEARCH RESULTS:\n{search_context}\n\n"
        )

    messages = [{"role": "system", "content": system_content}]
    messages.extend(stm_history)
    messages.append({"role": "user", "content": req.message})

    try:
        response = client.chat.completions.create(
            model=req.model,
            messages=messages
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        db.close()
        return {"reply": f"Error: {str(e)}"}

    # 5. SAVE MEMORY
    if not is_guest and "guest-session" not in req.conversation_id:
        msg_count = db.query(ChatHistory).filter(ChatHistory.conversation_id == req.conversation_id).count()
        if msg_count == 0:
            conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
            if conv: conv.title = req.message[:30] + "..."
        
        db.add(ChatHistory(conversation_id=req.conversation_id, role="user", content=req.message))
        db.add(ChatHistory(conversation_id=req.conversation_id, role="assistant", content=ai_reply))
        db.commit()
        add_to_ltm(f"User said: {req.message}", {"user_id": req.user_id})
        add_to_ltm(f"AI replied: {ai_reply}", {"user_id": req.user_id})

    db.close()
    return {"reply": ai_reply}