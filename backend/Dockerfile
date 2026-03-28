FROM python:3.10-slim

# Install necessary build tools for llama-cpp-python
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure models directory exists
RUN mkdir -p models

# Make startup script executable
RUN chmod +x start.sh

EXPOSE 8000

# start.sh downloads the model if missing, then runs uvicorn
CMD ["bash", "start.sh"]

