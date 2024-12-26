FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task

RUN yum update -y && \
    yum install -y libmagic poppler-utils tesseract libxml2-devel libxslt-devel && \
    yum clean all

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN yum install antiword abiword unrtf poppler-utils libjpeg-dev tesseract-ocr pstotext
RUN pip install fulltext
COPY . .

CMD ["api.main.mangum_app"]
