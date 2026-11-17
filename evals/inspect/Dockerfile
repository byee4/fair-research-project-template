FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest pyyaml jsonschema pandas ruff snakefmt
COPY . /repo
WORKDIR /repo
RUN git init -q && git add -A && git -c user.email=e@x -c user.name=eval commit -qm baseline
