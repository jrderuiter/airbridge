# Builder image, used for building our wheel.
FROM python:3.12-slim as builder

RUN pip install poetry==1.8.3

ENV POETRY_NO_INTERACTION=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY src ./src
RUN touch README.md

# RUN poetry build
RUN poetry build

# Runtime image containing Airflow in which we'll
# install our wheel. Note we also include Airflow
# in the pip install to avoid accidentally
# upgrading/downgrading Airflow.
FROM apache/airflow:2.10.1 as runtime

COPY docker/airflow/patches/airflow /home/airflow/.local/lib/python3.12/site-packages/airflow

COPY --from=builder /app/dist /tmp/dist
RUN python -m pip install --no-cache-dir \
    /tmp/dist/*.whl \
    apache-airflow==${AIRFLOW_VERSION}
