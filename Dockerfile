FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY config.yaml .

# Create volume mount points
VOLUME ["/app/config"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (if needed for future HTTP features)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
