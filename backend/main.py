from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from openai import OpenAI
from .database import init_db, SessionLocal, ChatHistory
from .memory import add_memory, query_memory
from .tools import search_internet
from datetime import datetime

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.mount("/static", StaticFiles(directory="frontend"), name="static")

class ChatRequest(BaseModel):
    message: str
    api_key: str
    model: str
    user_id: str
    use_search: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("frontend/index.html") as f:
        return f.read()

@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.api_key:
        raise HTTPException(status_code=400, detail="API Key is required")

    # 1. Intelligent Search Trigger
    # Automatically search if these keywords are found, or if user explicitly enabled it
    search_keywords = ["current", "latest", "today", "news", "weather", "time", "date", "recent", "who is", "where is"]
    should_search = req.use_search or any(keyword in req.message.lower() for keyword in search_keywords)

    search_context = ""
    if should_search:
        print(f"Searching internet for: {req.message}")
        search_context = search_internet(req.message)

    # 2. RAG Memory
    past_context = query_memory(req.message, req.user_id)
    
    # 3. Construct System Prompt
    system_prompt = "You are a helpful AI assistant.\n"
    
    # Inject Current Date/Time always
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt += f"\nCurrent System Date and Time: {current_time}\n"

    if search_context:
        system_prompt += f"\n***INTERNET SEARCH RESULTS***:\n{search_context}\n"
        system_prompt += "You MUST use the above search results to answer the user's question about current events or time.\n"
    
    if past_context:
        system_prompt += f"\nPast Conversation Context:\n{' '.join(past_context[0])}\n"

    # 4. Call OpenRouter
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=req.api_key,
        )
        response = client.chat.completions.create(
            model=req.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": req.message}
            ]
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        return {"reply": f"Error calling AI Model: {str(e)}"}

    # 5. Save Memory
    add_memory(req.message, {"user_id": req.user_id, "type": "query"})
    add_memory(ai_reply, {"user_id": req.user_id, "type": "response"})

    # 6. Log to SQLite
    db = SessionLocal()
    try:
        log = ChatHistory(user_email=req.user_id, role="user", content=req.message)
        db.add(log)
        log = ChatHistory(user_email=req.user_id, role="ai", content=ai_reply)
        db.add(log)
        db.commit()
    finally:
        db.close()

    return {"reply": ai_reply}