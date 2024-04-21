# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster


# Set the working directory in the container
WORKDIR /app
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--port", "8000", "--host", "0.0.0.0"]
