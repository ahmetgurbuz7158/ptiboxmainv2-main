# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ptiboxmainv2-main/ .

ENV PORT=8080

CMD ["python", "app.py"] 