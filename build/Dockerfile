FROM python:3.9.1-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install \
    'ffmpeg' \
    'libsm6' \
    'libxext6' -y

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

EXPOSE 8080

CMD ["python", "main.py"]
