FROM python:3.9-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
[cite_start]RUN pip install --no-cache-dir -r requirements.txt # [cite: 132]
COPY main.py .
CMD ["python", "./main.py"]