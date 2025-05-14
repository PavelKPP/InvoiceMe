FROM python:3.11-slim

# System dependencies for PDF generation and Firebase
RUN apt-get update && \
    apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# First copy only requirements for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY handlers/ ./handlers/
COPY services/ ./services/
COPY bot.py config.py ./ 

# Create and switch to non-root user
RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

# Set Python path
ENV PYTHONPATH=/app

# Run your bot
CMD ["python", "bot.py"]