FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
COPY *.sh .
RUN pip install Pillow numpy flask-cors
RUN chmod +x *.sh 2>/dev/null || true
EXPOSE 5050 5060
