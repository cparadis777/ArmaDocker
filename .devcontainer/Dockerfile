FROM debian:bookworm-slim

# Install required apt packages similar to project Dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        lib32stdc++6 \
        lib32gcc-s1 \
        libcurl4 \
        wget \
        ca-certificates \
        curl \
        libstdc++6 \
        libssl3 \
        libc6 \
        git \
        zip \
        unzip \
        python3 \
        python3-pip \
        python3.11-venv \
        podman \
    && rm -rf /var/lib/apt/lists/*

# Download DepotDownloader (kept for parity with project runtime)
RUN wget https://github.com/SteamRE/DepotDownloader/releases/latest/download/DepotDownloader-linux-x64.zip -O /tmp/depotdownloader.zip \
    && mkdir -p /usr/bin/depotdownloader \
    && unzip /tmp/depotdownloader.zip -d /opt/depotdownloader \
    && rm /tmp/depotdownloader.zip

# Project Python dependencies used by the repo
RUN mkdir /opt/arma
WORKDIR /opt/arma
RUN python3 -m venv .venv
