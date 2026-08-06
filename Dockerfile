FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR /app

# Install PyTorch CPU version
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy and install Python dependencies
COPY ai-advisor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai-advisor/app ./app

# Copy knowledge base
COPY general_guides /knowledge/general_guides
COPY business_guides /knowledge/business_guides

# Set environment variables for the application
ENV SHOPSPACE_KNOWLEDGE_ROOT=/knowledge
ENV SHOPSPACE_STORAGE_DIR=/app/storage

# Expose the port used by Hugging Face Spaces
EXPOSE 7860

# Run the application
CMD ["sh", "-c", "python -m app.ingest && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
