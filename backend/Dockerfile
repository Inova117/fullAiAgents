FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy engine requirements and install dependencies
COPY ../engine/requirements.txt ./engine_requirements.txt
RUN pip install --no-cache-dir -r engine_requirements.txt

# Copy the backend application code
COPY app/ ./app/

# Copy the engine directory (needed for pipeline execution)
COPY ../engine/ ./engine/

# Create data directories
RUN mkdir -p /app/data/exports
RUN mkdir -p /app/engine/data

# Expose port
EXPOSE 8000

# Run the application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
