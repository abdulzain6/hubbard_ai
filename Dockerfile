FROM public.ecr.aws/lambda/python:3.11

WORKDIR /var/task

RUN yum update -y && \
    yum install -y libmagic poppler-utils tesseract libxml2-devel libxslt-devel && \
    yum clean all

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["api.main.mangum_app"]
