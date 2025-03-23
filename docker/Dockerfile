FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY weatherbot.py .

CMD ["python", "weatherbot.py"] 