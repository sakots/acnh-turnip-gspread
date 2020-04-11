FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system
COPY . ./
ENTRYPOINT ["/entrypoint.sh"]
