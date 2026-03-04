FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# The model file should be mounted or copied into /app/models
ENV MODEL_PATH=models/ECE-Qwen0.5B-FT-V2.Q2_K.gguf \
    N_CTX=4096 \
    N_GPU_LAYERS=0

EXPOSE 8000

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]

