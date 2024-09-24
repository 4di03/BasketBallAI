FROM python:3.9.13
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD gunicorn --bind 127.0.0.1:5000 --workers 1 --worker-class eventlet app:app