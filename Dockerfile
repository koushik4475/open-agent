FROM python:3.11-slim

RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng libglib2.0-0 libsm6 libxrender1 libxext6 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs data/chroma_db uploads

ENV PYTHONPATH=/app
ENV PORT=7860

EXPOSE 7860

CMD ["python", "openagent/ui/server.py"]
