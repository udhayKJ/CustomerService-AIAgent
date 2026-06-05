# ==========================================
# STAGE 1: Download Ollama Models
# ==========================================
FROM ollama/ollama:latest AS model-builder

# Start Ollama server in background, wait for it, and pull models
RUN ollama serve & \
    sleep 5 && \
    ollama pull gemma2:2b && \
    ollama pull nomic-embed-text:latest

# ==========================================
# STAGE 2: Final Runtime Image
# ==========================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy Ollama binary, libraries, and the downloaded models from the builder stage
COPY --from=model-builder /usr/bin/ollama /usr/bin/ollama
COPY --from=model-builder /usr/lib/ollama /usr/lib/ollama
COPY --from=model-builder /root/.ollama /root/.ollama

# Install minimal OS dependencies for Python builds
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Remove build tools to keep the final image smaller
RUN apt-get purge -y --auto-remove build-essential

# Copy the rest of your application code
COPY . /app

# Expose ports: 8000 for your Python app, 11434 for Ollama
EXPOSE 8000 11434

# Start Ollama in the background, wait 3 seconds, then start the Python application
CMD sh -c "ollama serve & sleep 3 && python main.py"
