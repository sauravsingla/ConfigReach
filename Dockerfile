ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/configreach

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install . \
    && groupadd --system --gid 10001 configreach \
    && useradd --system --uid 10001 --gid configreach --create-home --home-dir /home/configreach --shell /usr/sbin/nologin configreach \
    && mkdir -p /workspace \
    && chown 10001:10001 /workspace /home/configreach

ENV HOME=/home/configreach
WORKDIR /workspace
USER 10001:10001

LABEL org.opencontainers.image.title="ConfigReach" \
      org.opencontainers.image.description="Deterministic configuration coverage for software repositories" \
      org.opencontainers.image.source="https://github.com/sauravsingla/ConfigReach" \
      org.opencontainers.image.licenses="MIT"

ENTRYPOINT ["configreach"]
CMD ["--help"]
