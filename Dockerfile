FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/configreach

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install .

WORKDIR /workspace

LABEL org.opencontainers.image.title="ConfigReach" \
      org.opencontainers.image.description="Deterministic configuration coverage for software repositories" \
      org.opencontainers.image.source="https://github.com/sauravsingla/ConfigReach" \
      org.opencontainers.image.licenses="MIT"

ENTRYPOINT ["configreach"]
CMD ["--help"]
