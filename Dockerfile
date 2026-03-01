# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies (Tesseract OCR + other tools)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for faster rebuilds)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Create necessary folders
RUN mkdir -p logs data/chroma_db uploads

# Expose port 7860 (Hugging Face uses this port)
EXPOSE 7860

# Set the PORT environment variable
ENV PORT=7860

# Start the Flask server
CMD ["python", "-m", "flask", "--app", "ui/server.py", "run", "--host", "0.0.0.0", "--port", "7860"]
