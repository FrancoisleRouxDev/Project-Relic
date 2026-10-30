FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY personas ./personas
RUN pip install .

RUN useradd --create-home relic && mkdir /data && chown relic /data
USER relic
VOLUME /data

# Run interactively: docker run -it --rm --env-file .env -v relic-data:/data relic
CMD ["python", "-m", "relic"]
