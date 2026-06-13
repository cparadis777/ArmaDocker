FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests \
    python3 \
    python3-venv \
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
    rename \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install DepotDownloader
RUN wget https://github.com/SteamRE/DepotDownloader/releases/latest/download/DepotDownloader-linux-x64.zip -O /tmp/depotdownloader.zip \
    && mkdir -p /tmp/depotdownloader \
    && unzip /tmp/depotdownloader.zip -d /tmp/depotdownloader \
    && mv /tmp/depotdownloader/DepotDownloader /usr/bin/DepotDownloader \
    && chmod +x /usr/bin/DepotDownloader \
    && rm -rf /tmp/depotdownloader*

# Create server directories and steam user
RUN useradd -m -u 1000 -s /bin/bash steam \
    && mkdir -p /server /home/steam/.local /logs /app \
    && chown -R steam:steam /server /home/steam /logs /app

# Set up Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY *.py /app/
RUN chown -R steam:steam /app

# Expose Arma 3 ports (UDP + TCP)
EXPOSE 2302/udp 2303/udp 2304/udp 2305/udp 2306/udp
EXPOSE 2302/tcp 2303/tcp 2304/tcp 2305/tcp 2306/tcp

# Ensure proper signal handling
STOPSIGNAL SIGINT

USER steam

CMD ["python3", "/app/launch.py"]
