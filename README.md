# “Agentic AI system with tool use + retrieval + external context : ReAct Agent

Based on the ReAct pattern (Reason + Act)

Think → Decide → Use tool → Observe → Repeat

An open-source, self-hosted AI Agent application with a clean, modern dark UI. This agent leverages the power of OpenRouter LLMs to provide intelligent conversation, real-time internet search capabilities, and persistent memory.

![Docker](https://img.shields.io/badge/Docker-Supported-blue) ![Python](https://img.shields.io/badge/Python-3.10-yellow) ![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)

## ✨ Key Features

1.  **Real-Time Internet Access**:
    - The agent autonomously decides when to search the internet using DuckDuckGo.
    - Provides up-to-date answers on news, weather, and current events.
    - Includes a "Safety Net" keyword trigger to force search for queries containing words like "latest", "news", or "today".

2.  **Hybrid Memory System**:
    - **Short-Term Memory (SQLite)**: Maintains context within a specific chat session.
    - **Long-Term Memory (ChromaDB)**: Stores semantic vectors of past interactions. The agent can recall relevant details from older chats.

3.  **Reasoning Agent Architecture**:
    - Uses a ReAct (Reason + Act) inspired loop. The LLM decides if a tool is needed, executes it, and synthesizes the answer.

4.  **User Profiles & Session Management**:
    - **Guest Mode**: Chat without saving history.
    - **User Mode**: Enter a name to save chat history and memories persistently.

5.  **Modern Dark UI**:
    - Clean, modular, centered dark interface.

---

## 🏗️ Architecture Flow

```text
User Input -> [FastAPI Backend]
   -> 1. Memory Retrieval (ChromaDB + SQLite)
   -> 2. Agent Reasoning (Decide Search?)
   -> 3. Tool Execution (DuckDuckGo)
   -> 4. Final Response Generation
   -> 5. Storage (Save History)
   -> Response to User
```

---

## 📂 Project Structure

```text
ai-chatbot-project/
├── backend/
│   ├── main.py           # Core Agent Logic
│   ├── database.py       # SQLite Models
│   ├── memory.py         # ChromaDB Logic
│   ├── tools.py          # Internet Search
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── Dockerfile
└── README.md

```

🚀 Getting Started
Prerequisites
Docker Desktop installed.
OpenRouter API Key.

1. Build

```bash
docker build -t ai-agent .
```

2. Run

```bash
docker run -p 8000:8000 -v C:\Users\Vin/data:/app/data ai-agent
```

3. Access
   Open browser to http://localhost:8000.

⚙️ Configuration
OpenRouter API Key: Required for AI.
Model Selection: Choose `StepFun 3.5 Flash` (Free) or others.
User Identity: Enter name to save history.

🛠️ Troubleshooting
404 Error on Conversations: Clear Browser Local Storage (F12 -> Application -> Local Storage -> Clear).
High RAM Usage: Create `.wslconfig` file to limit Docker memory to 6GB.

📜 License
MIT License.
