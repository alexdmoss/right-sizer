FROM python:3.7.4-alpine3.10 AS requirements
ADD . /app
WORKDIR /app
RUN pip install pipenv=='2018.11.26'
RUN pipenv lock -r > requirements.txt
RUN pipenv lock --dev -r > requirements-dev.txt

FROM python:3.7.4-alpine3.10 AS runtime-pips
COPY --from=requirements /app /app
WORKDIR /app
RUN pip install -r requirements.txt --no-use-pep517

# FROM python:3.7.4-alpine3.10 AS pytest
# COPY --from=runtime-pips /app /app
# COPY --from=runtime-pips /usr/local /usr/local
# RUN apk update --no-cache \
#   && apk upgrade \
#   && apk add gcc musl-dev
# WORKDIR /app
# RUN pip install -r requirements-dev.txt
# RUN /usr/local/bin/pytest

FROM python:3.7.4-alpine3.10
COPY --from=runtime-pips /app /app
COPY --from=runtime-pips /usr/local /usr/local
WORKDIR /app
ENTRYPOINT ["/usr/local/bin/python", "-u", "/app/main.py"]
