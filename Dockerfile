# 1. Use Python 3.10 Slim
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files (good practice)
# PYTHONUNBUFFERED: Ensures logs (like print statements) show up immediately in Docker logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Install system dependencies
# build-essential: Needed for compiling Python libraries (like ChromaDB/SentenceTransformers)
# sqlite3: Required for the database engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 7. Create data directories AND give permissions
# This ensures the container can write SQLite and ChromaDB files
RUN mkdir -p /app/data/chroma_db && chmod -R 777 /app/data

# 8. Expose port
EXPOSE 8000

# 9. Run the app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]