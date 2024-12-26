FROM python:3.11-slim

WORKDIR /var/task

RUN apt-get update && \
    apt-get install -y \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    libxml2-dev \
    libxslt-dev \
    antiword \
    abiword \
    unrtf \
    libjpeg-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fulltext
COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "./key.pem", "--ssl-certfile", "./cert.pem"]
