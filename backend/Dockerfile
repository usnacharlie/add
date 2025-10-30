FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 9500

# Run database initialization and start the application
CMD ["sh", "-c", "python3 -c 'from backend.config.database import init_db; init_db()' && uvicorn backend.main:app --host 0.0.0.0 --port 9500"]
