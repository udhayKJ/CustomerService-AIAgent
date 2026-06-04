# Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# Install build dependencies, then runtime deps if requirements.txt exists
#COPY requirements.txt ./

RUN apt-get update \
	&& apt-get install -y --no-install-recommends build-essential \
	&& pip install --no-cache-dir -r requirements.txt || true \
	&& apt-get remove -y build-essential \
	&& apt-get autoremove -y \
	&& rm -rf /var/lib/apt/lists/*

#Copy project
COPY . /app

# Expose default port (change if your app uses a different one)
EXPOSE 8000

# Default command: try common entry points
CMD ["sh", "-c", "if [ -f ./main.py ]; then python main.py; elif [ -f ./app.py ]; then python app.py; else exec \"/bin/sh\"; fi"]
