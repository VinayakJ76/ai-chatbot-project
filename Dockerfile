# Use Python 3.10 Slim
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# 1. Install system dependencies
# sqlite3 is required for ChromaDB
# build-essential is for compiling libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Application Code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 4. Create data directories AND give permissions
# This ensures the container can write to these folders
RUN mkdir -p /app/data/chroma_db && chmod -R 777 /app/data

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]