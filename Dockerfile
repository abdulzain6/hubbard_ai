FROM python:3.11-slim

WORKDIR /var/task

RUN yum update -y && \
    yum install -y libmagic poppler-utils tesseract libxml2-devel libxslt-devel && \
    yum clean all

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN yum install antiword abiword unrtf poppler-utils libjpeg-dev tesseract-ocr pstotext
RUN pip install fulltext
COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
