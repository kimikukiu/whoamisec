FROM python:3.11-slim
WORKDIR /app

RUN mkdir -p /var/lib/jarvis

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir Pillow numpy flask-cors

COPY *.py .
COPY *.sh .
RUN chmod +x *.sh 2>/dev/null || true

EXPOSE 5050 5060

CMD ["python3", "cicada_ultimate.py"]
