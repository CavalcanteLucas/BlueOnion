# syntax=docker/dockerfile:1
FROM python:3.9-alpine
WORKDIR /codes
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN apk update
RUN apk add --no-cache python3-dev gcc libc-dev musl-dev linux-headers mariadb-connector-c-dev
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run"]