FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1

COPY . ./
RUN pip install pipenv && pipenv install --system

ENTRYPOINT ["/entrypoint.sh"]
