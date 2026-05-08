FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api ./api
COPY dashboard ./dashboard
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev,api,dashboard]"

COPY configs ./configs
COPY data/sample ./data/sample
COPY docs ./docs
COPY tests ./tests
COPY Makefile ./

CMD ["python", "-m", "src.cli", "--help"]

