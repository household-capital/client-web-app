FROM python:3.6-slim

SHELL ["/bin/bash", "-c"]

# Install basic tools
RUN set -euo pipefail; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      libmagic1 \
      zip \
      unzip; \
    rm -rf /var/lib/apt/lists/*
