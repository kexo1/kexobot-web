FROM python:3.11.4-slim-buster

WORKDIR /kexobot_web

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
EXPOSE 8000

CMD ["python", "KexoBOT_Web.py"]
