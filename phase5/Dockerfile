FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (e.g., for audio processing if needed)
RUN apt-get update && apt-get install -y gcc portaudio19-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "phase5.api.auth_service:app", "--host", "0.0.0.0", "--port", "8000"]
