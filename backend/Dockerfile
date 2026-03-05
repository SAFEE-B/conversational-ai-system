FROM python:3.10-slim

# Install necessary build tools for llama-cpp-python
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure models directory exists (the model gguf should be placed here)
RUN mkdir -p models

# Expose FastAPI port
EXPOSE 8000

# Run Uvicorn worker
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
